"""
Модуль для работы с YooMoney API
"""

import asyncio
import hashlib
import hmac
import json
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta
import httpx
from logger import bot_logger

@dataclass
class PaymentRequest:
    """Запрос на создание платежа"""
    amount: float
    currency: str = "RUB"
    description: str = ""
    return_url: str = ""
    payment_method_types: List[str] = None
    
    def __post_init__(self):
        if self.payment_method_types is None:
            self.payment_method_types = ["bank_card", "yoo_money"]

@dataclass
class PaymentResponse:
    """Ответ от YooMoney API"""
    id: str
    status: str
    paid: bool
    amount: Dict[str, Any]
    created_at: str
    description: str
    metadata: Dict[str, Any]
    payment_method: Optional[Dict[str, Any]] = None
    recipient: Optional[Dict[str, Any]] = None
    refundable: bool = False
    test: bool = False

class YooMoneyClient:
    """Клиент для работы с YooMoney API"""
    
    def __init__(self, client_id: str, secret_key: str = None):
        self.client_id = client_id
        self.secret_key = secret_key
        self.base_url = "https://api.yookassa.ru/v3"
        self.timeout = httpx.Timeout(30.0)
        
    async def _make_request(self, method: str, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Выполняет HTTP запрос к YooMoney API"""
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"Basic {self._get_auth_header()}",
            "Content-Type": "application/json",
            "Idempotence-Key": self._generate_idempotence_key()
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if method.upper() == "GET":
                    response = await client.get(url, headers=headers)
                elif method.upper() == "POST":
                    response = await client.post(url, headers=headers, json=data)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            bot_logger.log_system_error(e, f"YooMoney API error: {e.response.status_code}")
            raise Exception(f"YooMoney API error: {e.response.status_code}")
        except Exception as e:
            bot_logger.log_system_error(e, "YooMoney request failed")
            raise
    
    def _get_auth_header(self) -> str:
        """Создает заголовок авторизации"""
        import base64
        auth_string = f"{self.client_id}:{self.secret_key or ''}"
        return base64.b64encode(auth_string.encode()).decode()
    
    def _generate_idempotence_key(self) -> str:
        """Генерирует ключ идемпотентности"""
        return f"bot_{int(time.time() * 1000)}_{hashlib.md5(str(time.time()).encode()).hexdigest()[:8]}"
    
    async def create_payment(self, payment_request: PaymentRequest) -> PaymentResponse:
        """Создает новый платеж"""
        data = {
            "amount": {
                "value": f"{payment_request.amount:.2f}",
                "currency": payment_request.currency
            },
            "confirmation": {
                "type": "redirect",
                "return_url": payment_request.return_url
            },
            "description": payment_request.description,
            "payment_method_data": {
                "type": "bank_card"
            },
            "capture": True,
            "metadata": {
                "user_id": "bot_user",
                "created_at": datetime.now().isoformat()
            }
        }
        
        try:
            response_data = await self._make_request("POST", "/payments", data)
            
            return PaymentResponse(
                id=response_data["id"],
                status=response_data["status"],
                paid=response_data.get("paid", False),
                amount=response_data["amount"],
                created_at=response_data["created_at"],
                description=response_data.get("description", ""),
                metadata=response_data.get("metadata", {}),
                payment_method=response_data.get("payment_method"),
                recipient=response_data.get("recipient"),
                refundable=response_data.get("refundable", False),
                test=response_data.get("test", False)
            )
            
        except Exception as e:
            bot_logger.log_system_error(e, "Failed to create payment")
            raise
    
    async def get_payment(self, payment_id: str) -> PaymentResponse:
        """Получает информацию о платеже"""
        try:
            response_data = await self._make_request("GET", f"/payments/{payment_id}")
            
            return PaymentResponse(
                id=response_data["id"],
                status=response_data["status"],
                paid=response_data.get("paid", False),
                amount=response_data["amount"],
                created_at=response_data["created_at"],
                description=response_data.get("description", ""),
                metadata=response_data.get("metadata", {}),
                payment_method=response_data.get("payment_method"),
                recipient=response_data.get("recipient"),
                refundable=response_data.get("refundable", False),
                test=response_data.get("test", False)
            )
            
        except Exception as e:
            bot_logger.log_system_error(e, f"Failed to get payment {payment_id}")
            raise
    
    async def cancel_payment(self, payment_id: str) -> PaymentResponse:
        """Отменяет платеж"""
        try:
            response_data = await self._make_request("POST", f"/payments/{payment_id}/cancel")
            
            return PaymentResponse(
                id=response_data["id"],
                status=response_data["status"],
                paid=response_data.get("paid", False),
                amount=response_data["amount"],
                created_at=response_data["created_at"],
                description=response_data.get("description", ""),
                metadata=response_data.get("metadata", {}),
                payment_method=response_data.get("payment_method"),
                recipient=response_data.get("recipient"),
                refundable=response_data.get("refundable", False),
                test=response_data.get("test", False)
            )
            
        except Exception as e:
            bot_logger.log_system_error(e, f"Failed to cancel payment {payment_id}")
            raise

class PaymentManager:
    """Менеджер платежей для бота"""
    
    def __init__(self, client_id: str, secret_key: str = None):
        self.client = YooMoneyClient(client_id, secret_key)
        self.active_payments: Dict[str, Dict[str, Any]] = {}
    
    async def create_payment_for_user(self, user_id: int, amount: float, description: str = "") -> Dict[str, Any]:
        """Создает платеж для пользователя"""
        payment_request = PaymentRequest(
            amount=amount,
            description=description or f"Платеж от пользователя {user_id}",
            return_url="https://t.me/your_bot"  # Замените на ваш бот
        )
        
        try:
            payment = await self.client.create_payment(payment_request)
            
            # Сохраняем информацию о платеже
            self.active_payments[payment.id] = {
                "user_id": user_id,
                "amount": amount,
                "status": payment.status,
                "created_at": datetime.now(),
                "payment_url": payment.metadata.get("payment_url")
            }
            
            bot_logger.log_user_action(user_id, "payment_created", {
                "payment_id": payment.id,
                "amount": amount,
                "status": payment.status
            })
            
            return {
                "payment_id": payment.id,
                "status": payment.status,
                "amount": payment.amount,
                "confirmation_url": payment.metadata.get("confirmation_url"),
                "created_at": payment.created_at
            }
            
        except Exception as e:
            bot_logger.log_system_error(e, f"Failed to create payment for user {user_id}")
            raise
    
    async def check_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """Проверяет статус платежа"""
        try:
            payment = await self.client.get_payment(payment_id)
            
            # Обновляем локальную информацию
            if payment_id in self.active_payments:
                self.active_payments[payment_id]["status"] = payment.status
                self.active_payments[payment_id]["paid"] = payment.paid
            
            return {
                "payment_id": payment.id,
                "status": payment.status,
                "paid": payment.paid,
                "amount": payment.amount,
                "created_at": payment.created_at
            }
            
        except Exception as e:
            bot_logger.log_system_error(e, f"Failed to check payment status {payment_id}")
            raise
    
    async def process_webhook(self, webhook_data: Dict[str, Any]) -> bool:
        """Обрабатывает webhook от YooMoney"""
        try:
            payment_id = webhook_data.get("object", {}).get("id")
            if not payment_id:
                return False
            
            # Проверяем статус платежа
            payment_info = await self.check_payment_status(payment_id)
            
            if payment_info["paid"] and payment_id in self.active_payments:
                user_id = self.active_payments[payment_id]["user_id"]
                
                # Здесь можно добавить логику начисления очков/премиум статуса
                bot_logger.log_user_action(user_id, "payment_completed", {
                    "payment_id": payment_id,
                    "amount": payment_info["amount"]
                })
                
                # Удаляем из активных платежей
                del self.active_payments[payment_id]
                
                return True
            
            return False
            
        except Exception as e:
            bot_logger.log_system_error(e, "Failed to process webhook")
            return False
    
    def get_payment_url(self, payment_id: str) -> Optional[str]:
        """Получает URL для оплаты"""
        if payment_id in self.active_payments:
            return self.active_payments[payment_id].get("payment_url")
        return None
    
    async def cleanup_expired_payments(self):
        """Очищает истекшие платежи"""
        now = datetime.now()
        expired_payments = []
        
        for payment_id, payment_info in self.active_payments.items():
            if now - payment_info["created_at"] > timedelta(hours=24):
                expired_payments.append(payment_id)
        
        for payment_id in expired_payments:
            try:
                await self.client.cancel_payment(payment_id)
                del self.active_payments[payment_id]
                bot_logger.logger.info(f"Cancelled expired payment {payment_id}")
            except Exception as e:
                bot_logger.log_system_error(e, f"Failed to cancel expired payment {payment_id}")

# Глобальный экземпляр менеджера платежей
payment_manager = PaymentManager(
    client_id="906B63FC5E6BD7825970D5ADFAF70203BE667B5359729D1162A7E33D0CFF38A1"
)

# Фоновая задача для очистки истекших платежей
async def cleanup_payments_task():
    """Фоновая задача для очистки истекших платежей"""
    while True:
        try:
            await payment_manager.cleanup_expired_payments()
            await asyncio.sleep(3600)  # Проверка каждый час
        except Exception as e:
            bot_logger.log_system_error(e, "Error in payment cleanup task")
            await asyncio.sleep(300)  # Повтор через 5 минут при ошибке
