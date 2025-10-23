"""
Система платежей в Telegram Stars
"""

from typing import Dict, Any, Optional
from aiogram.types import LabeledPrice, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from logger import bot_logger
from config import config

class TelegramStarsPayment:
    """Система платежей в Telegram Stars"""
    
    def __init__(self):
        self.currency = "XTR"  # Валюта Telegram Stars
        self.premium_price = 100  # Стоимость подписки в звездах
        self.premium_title = "⭐ Премиум подписка"
        self.premium_description = "Получите неограниченный доступ ко всем функциям бота на 30 дней"
        self.premium_payload = "premium_subscription_30_days"
    
    def create_payment_keyboard(self) -> InlineKeyboardMarkup:
        """Создает клавиатуру для оплаты в звездах"""
        builder = InlineKeyboardBuilder()
        builder.button(
            text=f"Оплатить {self.premium_price} ⭐",
            pay=True
        )
        return builder.as_markup()
    
    def create_payment_prices(self) -> list[LabeledPrice]:
        """Создает список цен для платежа"""
        return [LabeledPrice(label="XTR", amount=self.premium_price)]
    
    def create_payment_invoice_data(self) -> Dict[str, Any]:
        """Создает данные для выставления счета"""
        return {
            "title": self.premium_title,
            "description": self.premium_description,
            "prices": self.create_payment_prices(),
            "provider_token": "",  # Для Telegram Stars пустая строка
            "payload": self.premium_payload,
            "currency": self.currency,
            "reply_markup": self.create_payment_keyboard()
        }
    
    def create_pay_support_keyboard(self) -> InlineKeyboardMarkup:
        """Создает клавиатуру для поддержки платежей"""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="💬 Связаться с поддержкой", url="https://t.me/d_kolesov")],
                [InlineKeyboardButton(text="📋 Условия возврата", callback_data="refund_terms")],
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")]
            ]
        )
    
    def get_refund_terms(self) -> str:
        """Возвращает условия возврата средств"""
        return """
📋 УСЛОВИЯ ВОЗВРАТА СРЕДСТВ

💎 Премиум подписка:
• Возврат возможен в течение 24 часов после покупки
• Причина: технические проблемы или ошибка при покупке
• Обработка заявки: до 48 часов

❌ НЕ подлежат возврату:
• Использованные функции подписки
• Пробный день (бесплатный)
• Донаты и поддержка проекта

📞 Для возврата средств:
• Свяжитесь с поддержкой: @d_kolesov
• Укажите ID платежа и причину возврата
• Приложите скриншот чека

⚖️ Окончательное решение:
Администратор оставляет за собой право отказать в возврате при нарушении условий использования.
"""

# Глобальный экземпляр системы платежей в звездах
stars_payment = TelegramStarsPayment()
