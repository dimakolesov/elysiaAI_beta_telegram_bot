"""
Система логирования для бота
"""

import logging
import sys
import os
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

class BotLogger:
    """Класс для логирования событий бота"""
    
    def __init__(self, log_level: str = "INFO"):
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)
        self.setup_logging()
    
    def setup_logging(self):
        """Настройка системы логирования"""
        # Создаем директорию для логов
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Формат логов
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Основной логгер
        self.logger = logging.getLogger('elysia_bot')
        self.logger.setLevel(self.log_level)
        
        # Очищаем существующие обработчики
        self.logger.handlers.clear()
        
        # Обработчик для файла
        file_handler = logging.FileHandler(
            log_dir / f"bot_{datetime.now().strftime('%Y%m%d')}.log",
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        
        # Обработчик для консоли
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        # Обработчик для ошибок
        error_handler = logging.FileHandler(
            log_dir / f"errors_{datetime.now().strftime('%Y%m%d')}.log",
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        
        # Добавляем обработчики
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        self.logger.addHandler(error_handler)
        
        # Логгер для безопасности
        self.security_logger = logging.getLogger('elysia_security')
        self.security_logger.setLevel(logging.WARNING)
        
        security_handler = logging.FileHandler(
            log_dir / f"security_{datetime.now().strftime('%Y%m%d')}.log",
            encoding='utf-8'
        )
        security_handler.setFormatter(formatter)
        self.security_logger.addHandler(security_handler)
    
    def log_message(self, user_id: int, message: str, message_type: str = "text"):
        """Логирование сообщения пользователя"""
        self.logger.info(f"User {user_id} sent {message_type}: {message[:100]}...")
    
    def log_command(self, user_id: int, command: str, args: Optional[str] = None):
        """Логирование команды"""
        args_str = f" with args: {args}" if args else ""
        self.logger.info(f"User {user_id} executed command: {command}{args_str}")
    
    def log_callback(self, user_id: int, callback_data: str):
        """Логирование callback запроса"""
        self.logger.info(f"User {user_id} pressed button: {callback_data}")
    
    def log_admin_action(self, action: str, metadata: Dict[str, Any] = None):
        """Логирование админ действий"""
        self.logger.warning(f"Admin action: {action}", extra={"metadata": metadata or {}})
    
    def log_api_request(self, endpoint: str, status_code: int, response_time: float):
        """Логирование API запроса"""
        self.logger.info(f"API {endpoint}: {status_code} ({response_time:.2f}s)")
    
    def log_database_operation(self, operation: str, table: str, user_id: Optional[int] = None):
        """Логирование операции с БД"""
        user_str = f" for user {user_id}" if user_id else ""
        self.logger.debug(f"DB {operation} on {table}{user_str}")
    
    def log_security_event(self, event_type: str, user_id: int, details: str):
        """Логирование событий безопасности"""
        self.security_logger.warning(f"SECURITY {event_type}: User {user_id} - {details}")
    
    def log_rate_limit(self, user_id: int, request_type: str, blocked: bool = False):
        """Логирование rate limiting"""
        action = "BLOCKED" if blocked else "LIMITED"
        self.security_logger.warning(f"RATE_LIMIT {action}: User {user_id} - {request_type}")
    
    def log_validation_error(self, user_id: int, error_type: str, input_data: str):
        """Логирование ошибок валидации"""
        self.security_logger.warning(f"VALIDATION_ERROR: User {user_id} - {error_type}: {input_data[:50]}...")
    
    def log_system_error(self, error: Exception, context: str = ""):
        """Логирование системных ошибок"""
        self.logger.error(f"SYSTEM_ERROR: {context} - {str(error)}", exc_info=True)
    
    def log_performance(self, operation: str, duration: float, user_id: Optional[int] = None):
        """Логирование производительности"""
        user_str = f" for user {user_id}" if user_id else ""
        self.logger.info(f"PERFORMANCE: {operation} took {duration:.2f}s{user_str}")
    
    def log_user_action(self, user_id: int, action: str, details: Optional[Dict[str, Any]] = None):
        """Логирование действий пользователя"""
        details_str = f" - {details}" if details else ""
        self.logger.info(f"USER_ACTION: User {user_id} - {action}{details_str}")
    
    def log_bot_response(self, user_id: int, response: str, response_time: float):
        """Логирование ответа бота"""
        self.logger.info(f"Bot response to user {user_id}: {response[:100]}... (took {response_time:.2f}s)")
    
    def log_startup(self, version: str = "1.0.0"):
        """Логирование запуска бота"""
        self.logger.info(f"Elysia AI Bot started - Version {version}")
    
    def log_shutdown(self):
        """Логирование остановки бота"""
        self.logger.info("Elysia AI Bot stopped")

# Глобальный экземпляр логгера
bot_logger = BotLogger()

# Декоратор для логирования производительности
def log_performance(operation_name: str):
    """Декоратор для логирования времени выполнения функций"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = datetime.now()
            try:
                result = await func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds()
                bot_logger.log_performance(operation_name, duration)
                return result
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                bot_logger.log_system_error(e, f"{operation_name} failed after {duration:.2f}s")
                raise
        return wrapper
    return decorator
