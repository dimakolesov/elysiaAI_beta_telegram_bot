"""
Система платежей для бота
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
from yoomoney import payment_manager, PaymentRequest
from logger import bot_logger

class PaymentType(Enum):
    """Типы платежей"""
    PREMIUM_SUBSCRIPTION = "premium_subscription"
    HEARTS_PACK = "hearts_pack"
    PREMIUM_FEATURES = "premium_features"
    DONATION = "donation"

@dataclass
class PaymentPlan:
    """План платежа"""
    id: str
    name: str
    description: str
    amount: float
    currency: str = "RUB"
    payment_type: PaymentType = PaymentType.HEARTS_PACK
    benefits: List[str] = None
    duration_days: int = 0  # 0 = разовый платеж
    
    def __post_init__(self):
        if self.benefits is None:
            self.benefits = []

class PaymentPlans:
    """Доступные планы платежей"""
    
    PLANS = {
        "premium_month": PaymentPlan(
            id="premium_month",
            name="⭐ Премиум подписка",
            description="Премиум подписка на 30 дней",
            amount=169.0,
            payment_type=PaymentType.PREMIUM_SUBSCRIPTION,
            benefits=[
                "Неограниченные сообщения", 
                "Приоритетная поддержка", 
                "Эксклюзивные функции",
                "Доступ к играм и развлечениям",
                "Персонализация бота"
            ],
            duration_days=30
        )
    }
    
    @classmethod
    def get_plan(cls, plan_id: str) -> Optional[PaymentPlan]:
        """Получает план по ID"""
        return cls.PLANS.get(plan_id)
    
    @classmethod
    def get_plans_by_type(cls, payment_type: PaymentType) -> List[PaymentPlan]:
        """Получает планы по типу"""
        return [plan for plan in cls.PLANS.values() if plan.payment_type == payment_type]
    
    @classmethod
    def get_all_plans(cls) -> List[PaymentPlan]:
        """Получает все планы"""
        return list(cls.PLANS.values())

class PaymentProcessor:
    """Процессор платежей"""
    
    def __init__(self):
        self.payment_manager = payment_manager
    
    async def create_payment(self, user_id: int, plan_id: str) -> Dict[str, Any]:
        """Создает платеж для пользователя"""
        plan = PaymentPlans.get_plan(plan_id)
        if not plan:
            raise ValueError(f"Plan {plan_id} not found")
        
        try:
            # Создаем платеж через YooMoney
            payment_info = await self.payment_manager.create_payment_for_user(
                user_id=user_id,
                amount=plan.amount,
                description=plan.description
            )
            
            bot_logger.log_user_action(user_id, "payment_initiated", {
                "plan_id": plan_id,
                "amount": plan.amount,
                "payment_id": payment_info["payment_id"]
            })
            
            return {
                "success": True,
                "payment_id": payment_info["payment_id"],
                "amount": plan.amount,
                "currency": plan.currency,
                "description": plan.description,
                "confirmation_url": payment_info.get("confirmation_url"),
                "plan": {
                    "id": plan.id,
                    "name": plan.name,
                    "benefits": plan.benefits
                }
            }
            
        except Exception as e:
            bot_logger.log_system_error(e, f"Failed to create payment for user {user_id}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def process_payment_success(self, user_id: int, payment_id: str) -> Dict[str, Any]:
        """Обрабатывает успешный платеж"""
        try:
            # Проверяем статус платежа
            payment_info = await self.payment_manager.check_payment_status(payment_id)
            
            if not payment_info["paid"]:
                return {
                    "success": False,
                    "error": "Payment not completed"
                }
            
            # Получаем информацию о плане из активных платежей
            if payment_id not in self.payment_manager.active_payments:
                return {
                    "success": False,
                    "error": "Payment not found in active payments"
                }
            
            payment_data = self.payment_manager.active_payments[payment_id]
            plan_id = payment_data.get("plan_id")
            plan = PaymentPlans.get_plan(plan_id) if plan_id else None
            
            if not plan:
                return {
                    "success": False,
                    "error": "Plan not found"
                }
            
            # Применяем бонусы в зависимости от типа платежа
            result = await self._apply_payment_benefits(user_id, plan)
            
            bot_logger.log_user_action(user_id, "payment_completed", {
                "payment_id": payment_id,
                "plan_id": plan_id,
                "amount": payment_info["amount"]
            })
            
            return {
                "success": True,
                "benefits_applied": result,
                "plan": {
                    "id": plan.id,
                    "name": plan.name,
                    "benefits": plan.benefits
                }
            }
            
        except Exception as e:
            bot_logger.log_system_error(e, f"Failed to process payment success for user {user_id}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _apply_payment_benefits(self, user_id: int, plan: PaymentPlan) -> Dict[str, Any]:
        """Применяет бонусы от платежа"""
        from db import add_hearts, grant_access
        
        benefits_applied = []
        
        try:
            if plan.payment_type == PaymentType.HEARTS_PACK:
                # Начисляем сердечки
                hearts_amount = int(plan.amount / 1)  # 1 рубль = 1 сердечко
                await add_hearts(user_id, hearts_amount)
                benefits_applied.append(f"Начислено {hearts_amount} сердечек")
                
            elif plan.payment_type == PaymentType.PREMIUM_SUBSCRIPTION:
                # Предоставляем премиум доступ
                await grant_access(user_id, plan.duration_days)
                benefits_applied.append(f"Премиум доступ на {plan.duration_days} дней")
                
            elif plan.payment_type == PaymentType.DONATION:
                # Для донатов даем небольшой бонус
                await add_hearts(user_id, 10)
                benefits_applied.append("Бонус 10 сердечек за поддержку")
            
            return {
                "benefits": benefits_applied,
                "plan_type": plan.payment_type.value
            }
            
        except Exception as e:
            bot_logger.log_system_error(e, f"Failed to apply payment benefits for user {user_id}")
            raise
    
    async def get_payment_history(self, user_id: int) -> List[Dict[str, Any]]:
        """Получает историю платежей пользователя"""
        # Здесь можно добавить логику получения истории из БД
        return []
    
    async def cancel_payment(self, user_id: int, payment_id: str) -> Dict[str, Any]:
        """Отменяет платеж"""
        try:
            await self.payment_manager.client.cancel_payment(payment_id)
            
            bot_logger.log_user_action(user_id, "payment_cancelled", {
                "payment_id": payment_id
            })
            
            return {
                "success": True,
                "message": "Payment cancelled successfully"
            }
            
        except Exception as e:
            bot_logger.log_system_error(e, f"Failed to cancel payment {payment_id}")
            return {
                "success": False,
                "error": str(e)
            }

# Глобальный экземпляр процессора платежей
payment_processor = PaymentProcessor()
