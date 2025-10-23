"""
Улучшенная система конфигурации
"""

import os
from typing import Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv(os.path.join(os.path.dirname(__file__), "config.env"))

@dataclass
class DatabaseConfig:
    """Конфигурация базы данных"""
    path: str
    timeout: int = 30
    max_connections: int = 10

@dataclass
class APIConfig:
    """Конфигурация API"""
    telegram_token: str
    deepseek_api_key: str
    deepseek_base_url: str
    deepseek_model: str
    temperature: float
    max_tokens: int
    timeout: int = 30

@dataclass
class SecurityConfig:
    """Конфигурация безопасности"""
    max_message_length: int = 1000
    rate_limit_requests: int = 20
    rate_limit_window: int = 60
    block_duration: int = 300
    enable_validation: bool = True
    enable_rate_limiting: bool = True

@dataclass
class LoggingConfig:
    """Конфигурация логирования"""
    level: str = "INFO"
    enable_file_logging: bool = True
    enable_console_logging: bool = True
    log_rotation_days: int = 7
    max_log_size_mb: int = 10

@dataclass
class YooMoneyConfig:
    """Конфигурация YooMoney"""
    client_id: str
    secret_key: str = ""
    webhook_url: str = ""

@dataclass
class BotConfig:
    """Основная конфигурация бота"""
    database: DatabaseConfig
    api: APIConfig
    security: SecurityConfig
    logging: LoggingConfig
    yoomoney: YooMoneyConfig
    
    # Дополнительные настройки
    debug_mode: bool = False
    maintenance_mode: bool = False
    max_users: int = 10000
    cleanup_interval: int = 300

class ConfigManager:
    """Менеджер конфигурации"""
    
    def __init__(self):
        self.config = self._load_config()
        self._validate_config()
    
    def _load_config(self) -> BotConfig:
        """Загрузка конфигурации из переменных окружения"""
        
        # Проверяем наличие обязательных переменных
        required_vars = [
            'TELEGRAM_BOT_TOKEN',
            'DEEPSEEK_API_KEY',
            'DEEPSEEK_BASE_URL',
            'DEEPSEEK_MODEL'
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Отсутствуют обязательные переменные окружения: {', '.join(missing_vars)}")
        
        # Конфигурация базы данных
        database_config = DatabaseConfig(
            path=os.getenv('DB_PATH', './data.sqlite3'),
            timeout=int(os.getenv('DB_TIMEOUT', '30')),
            max_connections=int(os.getenv('DB_MAX_CONNECTIONS', '10'))
        )
        
        # Конфигурация API
        api_config = APIConfig(
            telegram_token=os.getenv('TELEGRAM_BOT_TOKEN'),
            deepseek_api_key=os.getenv('DEEPSEEK_API_KEY'),
            deepseek_base_url=os.getenv('DEEPSEEK_BASE_URL'),
            deepseek_model=os.getenv('DEEPSEEK_MODEL', 'deepseek-chat'),
            temperature=float(os.getenv('DEEPSEEK_TEMPERATURE', '0.7')),
            max_tokens=int(os.getenv('DEEPSEEK_MAX_TOKENS', '200')),
            timeout=int(os.getenv('API_TIMEOUT', '30'))
        )
        
        # Конфигурация безопасности
        security_config = SecurityConfig(
            max_message_length=int(os.getenv('MAX_MESSAGE_LENGTH', '1000')),
            rate_limit_requests=int(os.getenv('RATE_LIMIT_REQUESTS', '20')),
            rate_limit_window=int(os.getenv('RATE_LIMIT_WINDOW', '60')),
            block_duration=int(os.getenv('BLOCK_DURATION', '300')),
            enable_validation=os.getenv('ENABLE_VALIDATION', 'true').lower() == 'true',
            enable_rate_limiting=os.getenv('ENABLE_RATE_LIMITING', 'true').lower() == 'true'
        )
        
        # Конфигурация логирования
        logging_config = LoggingConfig(
            level=os.getenv('LOG_LEVEL', 'INFO'),
            enable_file_logging=os.getenv('ENABLE_FILE_LOGGING', 'true').lower() == 'true',
            enable_console_logging=os.getenv('ENABLE_CONSOLE_LOGGING', 'true').lower() == 'true',
            log_rotation_days=int(os.getenv('LOG_ROTATION_DAYS', '7')),
            max_log_size_mb=int(os.getenv('MAX_LOG_SIZE_MB', '10'))
        )
        
        # Конфигурация YooMoney
        yoomoney_config = YooMoneyConfig(
            client_id=os.getenv('YOOMONEY_CLIENT_ID', ''),
            secret_key=os.getenv('YOOMONEY_SECRET_KEY', ''),
            webhook_url=os.getenv('YOOMONEY_WEBHOOK_URL', '')
        )
        
        return BotConfig(
            database=database_config,
            api=api_config,
            security=security_config,
            logging=logging_config,
            yoomoney=yoomoney_config,
            debug_mode=os.getenv('DEBUG_MODE', 'false').lower() == 'true',
            maintenance_mode=os.getenv('MAINTENANCE_MODE', 'false').lower() == 'true',
            max_users=int(os.getenv('MAX_USERS', '10000')),
            cleanup_interval=int(os.getenv('CLEANUP_INTERVAL', '300'))
        )
    
    def _validate_config(self):
        """Валидация конфигурации"""
        # Проверяем токен Telegram
        if not self.config.api.telegram_token or len(self.config.api.telegram_token) < 10:
            raise ValueError("Неверный формат Telegram Bot Token")
        
        # Проверяем URL API
        if not self.config.api.deepseek_base_url.startswith(('http://', 'https://')):
            raise ValueError("Неверный формат URL API")
        
        # Проверяем параметры безопасности
        if self.config.security.max_message_length < 100:
            raise ValueError("Максимальная длина сообщения слишком мала")
        
        if self.config.security.rate_limit_requests < 1:
            raise ValueError("Лимит запросов должен быть больше 0")
        
        # Проверяем параметры логирования
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.config.logging.level.upper() not in valid_log_levels:
            raise ValueError(f"Неверный уровень логирования. Допустимые: {', '.join(valid_log_levels)}")
    
    def get_database_url(self) -> str:
        """Получить URL базы данных"""
        return f"sqlite:///{self.config.database.path}"
    
    def is_production(self) -> bool:
        """Проверка, что это production окружение"""
        return not self.config.debug_mode and not self.config.maintenance_mode
    
    def get_api_headers(self) -> Dict[str, str]:
        """Получить заголовки для API запросов"""
        return {
            "Authorization": f"Bearer {self.config.api.deepseek_api_key}",
            "Content-Type": "application/json",
            "User-Agent": "ElysiaAI-Bot/1.0.0"
        }
    
    def get_rate_limit_config(self) -> Dict[str, int]:
        """Получить конфигурацию rate limiting"""
        return {
            'max_requests': self.config.security.rate_limit_requests,
            'window_seconds': self.config.security.rate_limit_window,
            'block_duration': self.config.security.block_duration
        }
    
    def update_config(self, **kwargs):
        """Обновление конфигурации во время выполнения"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
    
    def get_config_dict(self) -> Dict[str, Any]:
        """Получить конфигурацию в виде словаря"""
        return {
            'database': {
                'path': self.config.database.path,
                'timeout': self.config.database.timeout,
                'max_connections': self.config.database.max_connections
            },
            'api': {
                'telegram_token': self.config.api.telegram_token[:10] + '...',  # Скрываем токен
                'deepseek_base_url': self.config.api.deepseek_base_url,
                'deepseek_model': self.config.api.deepseek_model,
                'temperature': self.config.api.temperature,
                'max_tokens': self.config.api.max_tokens,
                'timeout': self.config.api.timeout
            },
            'security': {
                'max_message_length': self.config.security.max_message_length,
                'rate_limit_requests': self.config.security.rate_limit_requests,
                'rate_limit_window': self.config.security.rate_limit_window,
                'block_duration': self.config.security.block_duration,
                'enable_validation': self.config.security.enable_validation,
                'enable_rate_limiting': self.config.security.enable_rate_limiting
            },
            'logging': {
                'level': self.config.logging.level,
                'enable_file_logging': self.config.logging.enable_file_logging,
                'enable_console_logging': self.config.logging.enable_console_logging,
                'log_rotation_days': self.config.logging.log_rotation_days,
                'max_log_size_mb': self.config.logging.max_log_size_mb
            },
            'bot': {
                'debug_mode': self.config.debug_mode,
                'maintenance_mode': self.config.maintenance_mode,
                'max_users': self.config.max_users,
                'cleanup_interval': self.config.cleanup_interval
            }
        }

# Глобальный экземпляр менеджера конфигурации
config_manager = ConfigManager()
config = config_manager.config
