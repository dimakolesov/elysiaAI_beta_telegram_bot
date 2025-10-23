"""
Система валидации данных для безопасности
"""

import re
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

class ValidationError(Exception):
    """Ошибка валидации данных"""
    pass

class MessageType(Enum):
    TEXT = "text"
    COMMAND = "command"
    CALLBACK = "callback"

@dataclass
class ValidationResult:
    """Результат валидации"""
    is_valid: bool
    error_message: Optional[str] = None
    sanitized_data: Optional[str] = None

class DataValidator:
    """Класс для валидации входящих данных"""
    
    def __init__(self):
        # Максимальная длина сообщения
        self.MAX_MESSAGE_LENGTH = 1000
        
        # Запрещенные паттерны (базовые)
        self.FORBIDDEN_PATTERNS = [
            r'<script.*?>.*?</script>',  # XSS
            r'javascript:',  # JavaScript injection
            r'data:text/html',  # Data URI injection
            r'vbscript:',  # VBScript injection
            r'on\w+\s*=',  # Event handlers
        ]
        
        # SQL injection паттерны
        self.SQL_INJECTION_PATTERNS = [
            r'union\s+select',
            r'drop\s+table',
            r'delete\s+from',
            r'insert\s+into',
            r'update\s+set',
            r'exec\s*\(',
            r'execute\s*\(',
            r'--',  # SQL comment
            r'/\*.*?\*/',  # SQL comment block
        ]
        
        # Спам паттерны
        self.SPAM_PATTERNS = [
            r'(.)\1{10,}',  # Повторяющиеся символы
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',  # URLs
        ]
    
    def validate_message(self, text: str, message_type: MessageType = MessageType.TEXT) -> ValidationResult:
        """Валидация сообщения пользователя"""
        if not text:
            return ValidationResult(False, "Пустое сообщение")
        
        # Проверка длины
        if len(text) > self.MAX_MESSAGE_LENGTH:
            return ValidationResult(False, f"Сообщение слишком длинное (максимум {self.MAX_MESSAGE_LENGTH} символов)")
        
        # Проверка на запрещенные паттерны
        for pattern in self.FORBIDDEN_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return ValidationResult(False, "Обнаружен потенциально опасный контент")
        
        # Проверка на SQL injection
        for pattern in self.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return ValidationResult(False, "Обнаружена попытка SQL инъекции")
        
        # Проверка на спам
        for pattern in self.SPAM_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return ValidationResult(False, "Обнаружен спам")
        
        # Санитизация данных
        sanitized = self._sanitize_text(text)
        
        return ValidationResult(True, sanitized_data=sanitized)
    
    def validate_user_id(self, user_id: Any) -> ValidationResult:
        """Валидация ID пользователя"""
        try:
            user_id = int(user_id)
            if user_id <= 0:
                return ValidationResult(False, "Неверный ID пользователя")
            return ValidationResult(True, sanitized_data=str(user_id))
        except (ValueError, TypeError):
            return ValidationResult(False, "ID пользователя должен быть числом")
    
    def validate_points(self, points: Any) -> ValidationResult:
        """Валидация очков"""
        try:
            points = int(points)
            if points < -1000 or points > 1000:  # Разумные ограничения
                return ValidationResult(False, "Недопустимое количество очков")
            return ValidationResult(True, sanitized_data=str(points))
        except (ValueError, TypeError):
            return ValidationResult(False, "Очки должны быть числом")
    
    def validate_gender(self, gender: str) -> ValidationResult:
        """Валидация пола"""
        if gender not in ['male', 'female']:
            return ValidationResult(False, "Неверный пол")
        return ValidationResult(True, sanitized_data=gender)
    
    def validate_mood(self, mood: str) -> ValidationResult:
        """Валидация настроения"""
        valid_moods = ['happy', 'sad', 'playful', 'caring', 'romantic', 'shy', 'sarcastic', 'thoughtful', 'excited', 'melancholic', 'mischievous', 'nostalgic']
        if mood not in valid_moods:
            return ValidationResult(False, "Неверное настроение")
        return ValidationResult(True, sanitized_data=mood)
    
    def validate_relationship_level(self, level: Any) -> ValidationResult:
        """Валидация уровня отношений"""
        try:
            level = int(level)
            if level < 1 or level > 5:
                return ValidationResult(False, "Уровень отношений должен быть от 1 до 5")
            return ValidationResult(True, sanitized_data=str(level))
        except (ValueError, TypeError):
            return ValidationResult(False, "Уровень отношений должен быть числом")
    
    def _sanitize_text(self, text: str) -> str:
        """Санитизация текста"""
        # Удаляем потенциально опасные символы
        text = re.sub(r'[<>"\']', '', text)
        
        # Ограничиваем длину
        text = text[:self.MAX_MESSAGE_LENGTH]
        
        # Удаляем лишние пробелы
        text = ' '.join(text.split())
        
        return text.strip()
    
    def validate_api_key(self, api_key: str) -> ValidationResult:
        """Валидация API ключа"""
        if not api_key:
            return ValidationResult(False, "API ключ не может быть пустым")
        
        if len(api_key) < 10:
            return ValidationResult(False, "API ключ слишком короткий")
        
        # Проверяем формат Telegram Bot Token
        if api_key.startswith('bot'):
            if not re.match(r'^\d+:[A-Za-z0-9_-]{35}$', api_key):
                return ValidationResult(False, "Неверный формат Telegram Bot Token")
        
        return ValidationResult(True, sanitized_data=api_key)

# Глобальный экземпляр валидатора
validator = DataValidator()
