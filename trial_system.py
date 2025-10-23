"""
Система пробного дня для бота
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from db import get_user_trial_status, set_user_trial_status, grant_access
from logger import bot_logger

class TrialSystem:
    """Система пробного дня"""
    
    def __init__(self):
        self.trial_duration_hours = 24  # 24 часа пробного периода
    
    async def check_trial_eligibility(self, user_id: int) -> bool:
        """Проверяет, может ли пользователь получить пробный день"""
        try:
            # Проверяем, не использовал ли пользователь уже пробный день
            trial_status = await get_user_trial_status(user_id)
            
            if trial_status is None:
                # Пользователь еще не получал пробный день
                return True
            elif trial_status == "used":
                # Пользователь уже использовал пробный день
                return False
            elif trial_status == "active":
                # Пробный день уже активен
                return False
            else:
                return True
                
        except Exception as e:
            bot_logger.log_system_error(e, f"Failed to check trial eligibility for user {user_id}")
            return False
    
    async def activate_trial(self, user_id: int) -> Dict[str, Any]:
        """Активирует пробный день для пользователя"""
        try:
            # Проверяем право на пробный день
            if not await self.check_trial_eligibility(user_id):
                return {
                    "success": False,
                    "error": "Trial already used or active"
                }
            
            # Активируем пробный день
            await set_user_trial_status(user_id, "active")
            
            # Предоставляем доступ на 24 часа
            await grant_access(user_id, 1)  # 1 день доступа
            
            # Запускаем таймер для автоматического окончания пробного дня
            await self._schedule_trial_expiry(user_id)
            
            bot_logger.log_user_action(user_id, "trial_activated", {
                "duration_hours": self.trial_duration_hours
            })
            
            return {
                "success": True,
                "message": "Trial activated successfully",
                "duration_hours": self.trial_duration_hours
            }
            
        except Exception as e:
            bot_logger.log_system_error(e, f"Failed to activate trial for user {user_id}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _schedule_trial_expiry(self, user_id: int):
        """Планирует автоматическое окончание пробного дня"""
        # В реальном приложении здесь можно использовать Celery или другую систему задач
        # Для простоты просто логируем
        bot_logger.logger.info(f"Trial scheduled for expiry for user {user_id} in {self.trial_duration_hours} hours")
    
    async def check_trial_status(self, user_id: int) -> Dict[str, Any]:
        """Проверяет статус пробного дня пользователя"""
        try:
            trial_status = await get_user_trial_status(user_id)
            
            if trial_status is None:
                return {
                    "has_trial": False,
                    "trial_used": False,
                    "trial_active": False,
                    "can_get_trial": True
                }
            elif trial_status == "used":
                return {
                    "has_trial": True,
                    "trial_used": True,
                    "trial_active": False,
                    "can_get_trial": False
                }
            elif trial_status == "active":
                return {
                    "has_trial": True,
                    "trial_used": False,
                    "trial_active": True,
                    "can_get_trial": False
                }
            else:
                return {
                    "has_trial": False,
                    "trial_used": False,
                    "trial_active": False,
                    "can_get_trial": True
                }
                
        except Exception as e:
            bot_logger.log_system_error(e, f"Failed to check trial status for user {user_id}")
            return {
                "has_trial": False,
                "trial_used": False,
                "trial_active": False,
                "can_get_trial": False
            }
    
    async def expire_trial(self, user_id: int) -> bool:
        """Завершает пробный день пользователя"""
        try:
            await set_user_trial_status(user_id, "used")
            
            bot_logger.log_user_action(user_id, "trial_expired", {})
            
            return True
            
        except Exception as e:
            bot_logger.log_system_error(e, f"Failed to expire trial for user {user_id}")
            return False

# Глобальный экземпляр системы пробного дня
trial_system = TrialSystem()
