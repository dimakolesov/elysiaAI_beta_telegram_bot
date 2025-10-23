"""
Реферальная система для бота
"""

from typing import Dict, List, Tuple, Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db import (
    get_referral_stats, get_referral_link, process_referral, 
    process_subscription_referral, get_referral_leaderboard, has_referrer
)
from logger import bot_logger

class ReferralSystem:
    """Система рефералов"""
    
    COMMISSION_RATE = 0.5  # 50% комиссия
    SUBSCRIPTION_PRICE = 169.0  # Стоимость подписки
    
    def __init__(self):
        self.bot_username = "elysia_ai_bot"  # Замените на реальный username бота
    
    async def get_referral_info(self, user_id: int) -> Dict:
        """Получить информацию о рефералах пользователя"""
        stats = await get_referral_stats(user_id)
        referral_link = await get_referral_link(user_id)
        
        return {
            'stats': stats,
            'link': referral_link,
            'commission_rate': self.COMMISSION_RATE,
            'subscription_price': self.SUBSCRIPTION_PRICE
        }
    
    async def create_referral_keyboard(self, user_id: int) -> InlineKeyboardMarkup:
        """Создать клавиатуру для реферальной системы"""
        stats = await get_referral_stats(user_id)
        
        buttons = [
            [InlineKeyboardButton(text="📊 Моя статистика", callback_data="referral_stats")],
            [InlineKeyboardButton(text="🔗 Скопировать ссылку", callback_data="copy_referral_link")],
            [InlineKeyboardButton(text="🏆 Топ рефереров", callback_data="referral_leaderboard")],
            [InlineKeyboardButton(text="❓ Как это работает?", callback_data="referral_help")],
            [InlineKeyboardButton(text="⬅️ Главное меню", callback_data="main_menu")]
        ]
        
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    async def get_referral_stats_text(self, user_id: int) -> str:
        """Получить текст статистики рефералов"""
        stats = await get_referral_stats(user_id)
        referral_link = await get_referral_link(user_id)
        
        text = f"💰 Зарабатывай вместе с нами\n\n"
        text += f"📊 Твоя статистика:\n"
        text += f"• Всего приглашено: {stats['total_referrals']}\n"
        text += f"• Активных рефералов: {stats['active_referrals']}\n"
        text += f"• Заработано: {stats['total_earnings']:.2f} ₽\n\n"
        
        if stats['last_commission_at']:
            text += f"💸 Последняя комиссия: {stats['last_commission_at']}\n\n"
        
        text += f"🔗 Твоя реферальная ссылка:\n"
        text += f"`{referral_link}`\n\n"
        text += f"💡 За каждого приглашенного пользователя, который оформит подписку, ты получишь {self.COMMISSION_RATE * 100}% от стоимости подписки ({self.SUBSCRIPTION_PRICE * self.COMMISSION_RATE:.2f} ₽)!"
        
        return text
    
    async def get_leaderboard_text(self) -> str:
        """Получить текст топа рефереров"""
        leaderboard = await get_referral_leaderboard(10)
        
        text = "🏆 Топ рефереров\n\n"
        
        if not leaderboard:
            text += "Пока никто не заработал на рефералах 😔\n"
            text += "Стань первым!"
        else:
            for i, (user_id, username, referrals, earnings) in enumerate(leaderboard, 1):
                username_display = f"@{username}" if username else f"ID: {user_id}"
                text += f"{i}. {username_display}\n"
                text += f"   👥 Рефералов: {referrals} | 💰 Заработано: {earnings:.2f} ₽\n\n"
        
        return text
    
    async def get_help_text(self) -> str:
        """Получить текст помощи по реферальной системе"""
        text = "❓ Как работает реферальная система?\n\n"
        text += "1️⃣ Скопируй свою реферальную ссылку\n"
        text += "2️⃣ Поделись ссылкой с друзьями\n"
        text += "3️⃣ Когда друг перейдет по ссылке и оформит подписку\n"
        text += "4️⃣ Ты получишь 50% от стоимости подписки!\n\n"
        text += f"💰 За каждого реферала: {self.SUBSCRIPTION_PRICE * self.COMMISSION_RATE:.2f} ₽\n"
        text += f"💎 Стоимость подписки: {self.SUBSCRIPTION_PRICE} ₽\n\n"
        text += "🎯 Чем больше друзей приведешь, тем больше заработаешь!\n"
        text += "💡 Рефералы могут приглашать своих друзей - и ты тоже получишь комиссию!"
        
        return text
    
    async def process_referral_registration(self, referred_id: int, referrer_id: int) -> bool:
        """Обработать регистрацию по реферальной ссылке"""
        try:
            # Проверяем, что пользователь еще не имеет реферера
            if await has_referrer(referred_id):
                return False
            
            # Проверяем, что пользователь не приглашает сам себя
            if referred_id == referrer_id:
                return False
            
            # Обрабатываем реферал
            success = await process_referral(referred_id, referrer_id)
            
            if success:
                bot_logger.log_info(f"Referral processed: {referrer_id} -> {referred_id}")
            
            return success
        except Exception as e:
            bot_logger.log_system_error(e, f"Failed to process referral: {referrer_id} -> {referred_id}")
            return False
    
    async def process_subscription_purchase(self, user_id: int) -> Optional[int]:
        """Обработать покупку подписки и вернуть ID реферера для выплаты комиссии"""
        try:
            referrer_id = await process_subscription_referral(user_id)
            
            if referrer_id:
                commission = self.SUBSCRIPTION_PRICE * self.COMMISSION_RATE
                bot_logger.log_info(f"Commission earned: {referrer_id} earned {commission} ₽ from {user_id}")
                
                return referrer_id
            
            return None
        except Exception as e:
            bot_logger.log_system_error(e, f"Failed to process subscription referral for {user_id}")
            return None

# Глобальный экземпляр системы рефералов
referral_system = ReferralSystem()
