"""
Система обработки ошибок
"""

import asyncio
import traceback
from typing import Optional, Callable, Any, Dict
from functools import wraps
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest, TelegramConflictError
from aiogram.types import Message, CallbackQuery
from logger import bot_logger

class BotError(Exception):
    """Базовый класс для ошибок бота"""
    def __init__(self, message: str, user_id: Optional[int] = None, error_code: Optional[str] = None):
        self.message = message
        self.user_id = user_id
        self.error_code = error_code
        super().__init__(message)

class ValidationError(BotError):
    """Ошибка валидации данных"""
    pass

class RateLimitError(BotError):
    """Ошибка превышения лимита запросов"""
    pass

class DatabaseError(BotError):
    """Ошибка базы данных"""
    pass

class APIError(BotError):
    """Ошибка внешнего API"""
    pass

class ErrorHandler:
    """Класс для обработки ошибок"""
    
    def __init__(self):
        self.error_messages = {
            'validation_error': "❌ Ваше сообщение содержит недопустимый контент. Пожалуйста, попробуйте еще раз.",
            'rate_limit_error': "⏰ Слишком много запросов. Подождите немного и попробуйте снова.",
            'database_error': "🔧 Временные технические проблемы. Попробуйте позже.",
            'api_error': "🌐 Проблемы с внешним сервисом. Попробуйте позже.",
            'telegram_error': "📱 Проблемы с Telegram. Попробуйте позже.",
            'unknown_error': "❓ Произошла неожиданная ошибка. Попробуйте позже."
        }
    
    async def handle_error(self, error: Exception, user_id: Optional[int] = None, context: str = "") -> str:
        """Обработка ошибки и возврат сообщения для пользователя"""
        
        # Логируем ошибку
        bot_logger.log_system_error(error, context)
        
        # Определяем тип ошибки и возвращаем соответствующее сообщение
        if isinstance(error, ValidationError):
            bot_logger.log_validation_error(user_id or 0, "validation", str(error))
            return self.error_messages['validation_error']
        
        elif isinstance(error, RateLimitError):
            bot_logger.log_rate_limit(user_id or 0, "general", blocked=True)
            return self.error_messages['rate_limit_error']
        
        elif isinstance(error, DatabaseError):
            bot_logger.log_database_operation("error", "unknown", user_id)
            return self.error_messages['database_error']
        
        elif isinstance(error, APIError):
            bot_logger.log_api_request("error", 500, 0.0)
            return self.error_messages['api_error']
        
        elif isinstance(error, TelegramAPIError):
            bot_logger.log_system_error(error, f"Telegram API error for user {user_id}")
            return self.error_messages['telegram_error']
        
        else:
            bot_logger.log_system_error(error, f"Unknown error for user {user_id}")
            return self.error_messages['unknown_error']
    
    async def send_error_message(self, message: Message, error: Exception, context: str = ""):
        """Отправка сообщения об ошибке пользователю"""
        try:
            user_message = await self.handle_error(error, message.from_user.id, context)
            await message.answer(user_message)
        except Exception as e:
            bot_logger.log_system_error(e, "Failed to send error message")
    
    async def send_error_callback(self, callback: CallbackQuery, error: Exception, context: str = ""):
        """Отправка сообщения об ошибке через callback"""
        try:
            user_message = await self.handle_error(error, callback.from_user.id, context)
            await callback.answer(user_message, show_alert=True)
        except Exception as e:
            bot_logger.log_system_error(e, "Failed to send error callback")

# Декораторы для обработки ошибок
def handle_errors(func: Callable) -> Callable:
    """Декоратор для автоматической обработки ошибок в функциях"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            error_handler = ErrorHandler()
            
            # Пытаемся найти user_id в аргументах
            user_id = None
            for arg in args:
                if hasattr(arg, 'from_user'):
                    user_id = arg.from_user.id
                    break
                elif hasattr(arg, 'user_id'):
                    user_id = arg.user_id
                    break
            
            # Логируем и обрабатываем ошибку
            await error_handler.handle_error(e, user_id, f"Error in {func.__name__}")
            
            # Если это Message или CallbackQuery, отправляем сообщение об ошибке
            for arg in args:
                if isinstance(arg, Message):
                    await error_handler.send_error_message(arg, e)
                    break
                elif isinstance(arg, CallbackQuery):
                    await error_handler.send_error_callback(arg, e)
                    break
    
    return wrapper

def handle_telegram_errors(func: Callable) -> Callable:
    """Декоратор для обработки ошибок Telegram API"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except TelegramConflictError as e:
            bot_logger.log_system_error(e, "Telegram conflict - multiple bot instances")
            # Не отправляем сообщение пользователю для конфликтов
        except TelegramBadRequest as e:
            bot_logger.log_system_error(e, "Telegram bad request")
            # Пытаемся отправить сообщение об ошибке
            for arg in args:
                if isinstance(arg, Message):
                    await arg.answer("❌ Некорректный запрос. Попробуйте еще раз.")
                    break
                elif isinstance(arg, CallbackQuery):
                    await arg.answer("❌ Некорректный запрос.", show_alert=True)
                    break
        except TelegramAPIError as e:
            bot_logger.log_system_error(e, "Telegram API error")
            # Пытаемся отправить сообщение об ошибке
            for arg in args:
                if isinstance(arg, Message):
                    await arg.answer("📱 Проблемы с Telegram. Попробуйте позже.")
                    break
                elif isinstance(arg, CallbackQuery):
                    await arg.answer("📱 Проблемы с Telegram.", show_alert=True)
                    break
    
    return wrapper

def retry_on_error(max_retries: int = 3, delay: float = 1.0):
    """Декоратор для повторных попыток при ошибках"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_error = None
            current_delay = delay  # Инициализируем локальную переменную
            
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        bot_logger.logger.warning(f"Attempt {attempt + 1} failed, retrying in {current_delay}s: {e}")
                        await asyncio.sleep(current_delay)
                        current_delay *= 2  # Экспоненциальная задержка
                    else:
                        bot_logger.log_system_error(e, f"All {max_retries} attempts failed")
            
            # Если все попытки неудачны, поднимаем последнюю ошибку
            raise last_error
        
        return wrapper
    return decorator

# Глобальный экземпляр обработчика ошибок
error_handler = ErrorHandler()

# Функции для создания специфических ошибок
def create_validation_error(message: str, user_id: Optional[int] = None) -> ValidationError:
    """Создание ошибки валидации"""
    return ValidationError(message, user_id, "VALIDATION_ERROR")

def create_rate_limit_error(user_id: int) -> RateLimitError:
    """Создание ошибки превышения лимита"""
    return RateLimitError("Rate limit exceeded", user_id, "RATE_LIMIT_ERROR")

def create_database_error(message: str, user_id: Optional[int] = None) -> DatabaseError:
    """Создание ошибки базы данных"""
    return DatabaseError(message, user_id, "DATABASE_ERROR")

def create_api_error(message: str, user_id: Optional[int] = None) -> APIError:
    """Создание ошибки API"""
    return APIError(message, user_id, "API_ERROR")
