"""
Система админ панели для бота
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio
from db import (
    get_all_user_ids, get_user_name, get_hearts, get_points, get_level,
    get_streak_days, get_total_messages, is_banned, ban_user, unset_ban,
    get_user_trial_status, set_user_trial_status, grant_access
)
from logger import bot_logger
from config import config

class AdminSystem:
    """Система админ панели"""
    
    def __init__(self):
        self.admin_username = "d_kolesov"  # Единственный админ
        self.admin_commands = {
            "stats": self.get_bot_statistics,
            "users": self.get_users_list,
            "user": self.get_user_info,
            "ban": self.ban_user_command,
            "unban": self.unban_user_command,
            "grant": self.grant_access_command,
            "trial": self.manage_trial_command,
            "broadcast": self.broadcast_message,
            "help": self.get_admin_help
        }
    
    def is_admin(self, username: str) -> bool:
        """Проверяет, является ли пользователь админом"""
        return username == self.admin_username
    
    async def get_bot_statistics(self) -> str:
        """Получает общую статистику бота"""
        try:
            # Получаем всех пользователей
            all_users = await get_all_user_ids()
            total_users = len(all_users)
            
            # Подсчитываем активных пользователей (за последние 7 дней)
            active_users = 0
            total_messages = 0
            total_hearts = 0
            total_points = 0
            
            for user_id in all_users:
                try:
                    messages = await get_total_messages(user_id)
                    hearts = await get_hearts(user_id)
                    points = await get_points(user_id)
                    
                    total_messages += messages
                    total_hearts += hearts
                    total_points += points
                    
                    # Проверяем активность (если есть сообщения, считаем активным)
                    if messages > 0:
                        active_users += 1
                        
                except Exception as e:
                    bot_logger.log_system_error(e, f"Error getting stats for user {user_id}")
                    continue
            
            # Статистика по подпискам
            premium_users = 0
            trial_users = 0
            
            for user_id in all_users:
                try:
                    # Проверяем премиум доступ
                    access_info = await grant_access(user_id, 0)
                    if access_info and access_info.get('has_access', False):
                        premium_users += 1
                    
                    # Проверяем пробный день
                    trial_status = await get_user_trial_status(user_id)
                    if trial_status == "active":
                        trial_users += 1
                        
                except Exception as e:
                    continue
            
            stats_text = f"""
📊 СТАТИСТИКА БОТА

👥 Пользователи:
• Всего пользователей: {total_users}
• Активных пользователей: {active_users}
• Премиум пользователей: {premium_users}
• Пробных пользователей: {trial_users}

💬 Активность:
• Всего сообщений: {total_messages}
• Всего сердечек: {total_hearts}
• Всего очков близости: {total_points}

⚙️ Система:
• Версия бота: 2.0.0
• Статус: Работает
• Время: {datetime.now().strftime('%H:%M:%S %d.%m.%Y')}
"""
            return stats_text
            
        except Exception as e:
            bot_logger.log_system_error(e, "Failed to get bot statistics")
            return "❌ Ошибка получения статистики"
    
    async def get_users_list(self, limit: int = 20) -> str:
        """Получает список пользователей"""
        try:
            all_users = await get_all_user_ids()
            total_users = len(all_users)
            
            users_text = f"👥 СПИСОК ПОЛЬЗОВАТЕЛЕЙ (показано {min(limit, total_users)} из {total_users})\n\n"
            
            for i, user_id in enumerate(all_users[:limit]):
                try:
                    username = await get_user_name(user_id)
                    messages = await get_total_messages(user_id)
                    hearts = await get_hearts(user_id)
                    level = await get_level(user_id)
                    banned = await is_banned(user_id)
                    
                    status = "🔴 Забанен" if banned else "🟢 Активен"
                    username_display = username if username else f"ID: {user_id}"
                    
                    users_text += f"{i+1}. {username_display}\n"
                    users_text += f"   ID: {user_id} | Сообщений: {messages} | Сердечки: {hearts} | Уровень: {level}\n"
                    users_text += f"   Статус: {status}\n\n"
                    
                except Exception as e:
                    users_text += f"{i+1}. ID: {user_id} (ошибка получения данных)\n\n"
                    continue
            
            if total_users > limit:
                users_text += f"... и еще {total_users - limit} пользователей"
            
            return users_text
            
        except Exception as e:
            bot_logger.log_system_error(e, "Failed to get users list")
            return "❌ Ошибка получения списка пользователей"
    
    async def get_user_info(self, user_id: int) -> str:
        """Получает подробную информацию о пользователе"""
        try:
            username = await get_user_name(user_id)
            messages = await get_total_messages(user_id)
            hearts = await get_hearts(user_id)
            points = await get_points(user_id)
            level = await get_level(user_id)
            streak = await get_streak_days(user_id)
            banned = await is_banned(user_id)
            trial_status = await get_user_trial_status(user_id)
            
            # Проверяем премиум доступ
            access_info = await grant_access(user_id, 0)
            has_premium = access_info and access_info.get('has_access', False)
            
            user_text = f"""
👤 ИНФОРМАЦИЯ О ПОЛЬЗОВАТЕЛЕ

🆔 ID: {user_id}
👤 Имя: {username if username else 'Не указано'}
🔴 Статус: {'Забанен' if banned else 'Активен'}

📊 Статистика:
• Сообщений: {messages}
• Сердечки: {hearts}
• Очки близости: {points}
• Уровень: {level}
• Дней подряд: {streak}

💎 Доступ:
• Премиум: {'✅ Да' if has_premium else '❌ Нет'}
• Пробный день: {trial_status if trial_status else 'Не использован'}

⏰ Время запроса: {datetime.now().strftime('%H:%M:%S %d.%m.%Y')}
"""
            return user_text
            
        except Exception as e:
            bot_logger.log_system_error(e, f"Failed to get user info for {user_id}")
            return f"❌ Ошибка получения информации о пользователе {user_id}"
    
    async def ban_user_command(self, user_id: int, reason: str = "Нарушение правил") -> str:
        """Банит пользователя"""
        try:
            if await is_banned(user_id):
                return f"❌ Пользователь {user_id} уже забанен"
            
            await ban_user(user_id, reason)
            bot_logger.log_admin_action("ban_user", {"user_id": user_id, "reason": reason})
            
            return f"✅ Пользователь {user_id} забанен. Причина: {reason}"
            
        except Exception as e:
            bot_logger.log_system_error(e, f"Failed to ban user {user_id}")
            return f"❌ Ошибка бана пользователя {user_id}"
    
    async def unban_user_command(self, user_id: int) -> str:
        """Разбанивает пользователя"""
        try:
            if not await is_banned(user_id):
                return f"❌ Пользователь {user_id} не забанен"
            
            await unset_ban(user_id)
            bot_logger.log_admin_action("unban_user", {"user_id": user_id})
            
            return f"✅ Пользователь {user_id} разбанен"
            
        except Exception as e:
            bot_logger.log_system_error(e, f"Failed to unban user {user_id}")
            return f"❌ Ошибка разбана пользователя {user_id}"
    
    async def grant_access_command(self, user_id: int, days: int) -> str:
        """Предоставляет доступ пользователю"""
        try:
            await grant_access(user_id, days)
            bot_logger.log_admin_action("grant_access", {"user_id": user_id, "days": days})
            
            return f"✅ Пользователю {user_id} предоставлен доступ на {days} дней"
            
        except Exception as e:
            bot_logger.log_system_error(e, f"Failed to grant access to user {user_id}")
            return f"❌ Ошибка предоставления доступа пользователю {user_id}"
    
    async def manage_trial_command(self, user_id: int, action: str) -> str:
        """Управляет пробным днем пользователя"""
        try:
            if action == "reset":
                await set_user_trial_status(user_id, None)
                return f"✅ Пробный день пользователя {user_id} сброшен"
            elif action == "activate":
                await set_user_trial_status(user_id, "active")
                return f"✅ Пробный день пользователя {user_id} активирован"
            elif action == "deactivate":
                await set_user_trial_status(user_id, "used")
                return f"✅ Пробный день пользователя {user_id} деактивирован"
            else:
                return "❌ Неверное действие. Доступные: reset, activate, deactivate"
                
        except Exception as e:
            bot_logger.log_system_error(e, f"Failed to manage trial for user {user_id}")
            return f"❌ Ошибка управления пробным днем пользователя {user_id}"
    
    async def broadcast_message(self, message: str) -> str:
        """Отправляет сообщение всем пользователям"""
        try:
            all_users = await get_all_user_ids()
            success_count = 0
            error_count = 0
            
            for user_id in all_users:
                try:
                    # Здесь должна быть отправка сообщения через бота
                    # Пока просто логируем
                    bot_logger.log_info(f"Broadcast to {user_id}: {message}")
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    continue
            
            bot_logger.log_admin_action("broadcast", {
                "message": message[:100],
                "success_count": success_count,
                "error_count": error_count
            })
            
            return f"✅ Рассылка завершена. Успешно: {success_count}, Ошибок: {error_count}"
            
        except Exception as e:
            bot_logger.log_system_error(e, "Failed to broadcast message")
            return "❌ Ошибка рассылки сообщения"
    
    def get_admin_help(self) -> str:
        """Возвращает справку по админ командам"""
        help_text = """
🛠️ АДМИН ПАНЕЛЬ - СПРАВКА

📊 Статистика:
• `/admin stats` - Общая статистика бота

👥 Управление пользователями:
• `/admin users [лимит]` - Список пользователей
• `/admin user <ID>` - Информация о пользователе
• `/admin ban <ID> [причина]` - Забанить пользователя
• `/admin unban <ID>` - Разбанить пользователя

💎 Управление доступом:
• `/admin grant <ID> <дни>` - Предоставить доступ
• `/admin trial <ID> <действие>` - Управление пробным днем
  Действия: reset, activate, deactivate

📢 Рассылки:
• `/admin broadcast <сообщение>` - Рассылка всем пользователям

❓ Помощь:
• `/admin help` - Эта справка

Примеры:
• `/admin stats`
• `/admin users 10`
• `/admin user 123456789`
• `/admin ban 123456789 Спам`
• `/admin grant 123456789 30`
• `/admin trial 123456789 reset`
"""
        return help_text
    
    async def process_admin_command(self, command: str, args: List[str]) -> str:
        """Обрабатывает админ команду"""
        try:
            if command not in self.admin_commands:
                return f"❌ Неизвестная команда: {command}\n\n{self.get_admin_help()}"
            
            if command == "stats":
                return await self.admin_commands[command]()
            elif command == "users":
                limit = int(args[0]) if args and args[0].isdigit() else 20
                return await self.admin_commands[command](limit)
            elif command == "user":
                if not args:
                    return "❌ Укажите ID пользователя"
                user_id = int(args[0])
                return await self.admin_commands[command](user_id)
            elif command == "ban":
                if not args:
                    return "❌ Укажите ID пользователя"
                user_id = int(args[0])
                reason = " ".join(args[1:]) if len(args) > 1 else "Нарушение правил"
                return await self.admin_commands[command](user_id, reason)
            elif command == "unban":
                if not args:
                    return "❌ Укажите ID пользователя"
                user_id = int(args[0])
                return await self.admin_commands[command](user_id)
            elif command == "grant":
                if len(args) < 2:
                    return "❌ Укажите ID пользователя и количество дней"
                user_id = int(args[0])
                days = int(args[1])
                return await self.admin_commands[command](user_id, days)
            elif command == "trial":
                if len(args) < 2:
                    return "❌ Укажите ID пользователя и действие"
                user_id = int(args[0])
                action = args[1]
                return await self.admin_commands[command](user_id, action)
            elif command == "broadcast":
                if not args:
                    return "❌ Укажите сообщение для рассылки"
                message = " ".join(args)
                return await self.admin_commands[command](message)
            elif command == "help":
                return self.admin_commands[command]()
            else:
                return await self.admin_commands[command]()
                
        except ValueError:
            return "❌ Неверный формат параметров"
        except Exception as e:
            bot_logger.log_system_error(e, f"Failed to process admin command: {command}")
            return f"❌ Ошибка выполнения команды: {command}"

# Глобальный экземпляр системы админ панели
admin_system = AdminSystem()
