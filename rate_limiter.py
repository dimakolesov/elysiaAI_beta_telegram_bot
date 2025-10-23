"""
Система ограничения скорости запросов (Rate Limiting)
"""

import time
import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict

@dataclass
class RateLimitConfig:
    """Конфигурация rate limiting"""
    max_requests: int = 10  # Максимум запросов
    window_seconds: int = 60  # Окно времени в секундах
    block_duration: int = 300  # Время блокировки в секундах (5 минут)

class RateLimiter:
    """Класс для ограничения скорости запросов"""
    
    def __init__(self):
        # Хранилище запросов пользователей
        self.user_requests: Dict[int, List[float]] = defaultdict(list)
        
        # Заблокированные пользователи
        self.blocked_users: Dict[int, float] = {}
        
        # Конфигурации для разных типов запросов
        self.configs = {
            'message': RateLimitConfig(max_requests=20, window_seconds=60),
            'command': RateLimitConfig(max_requests=10, window_seconds=60),
            'callback': RateLimitConfig(max_requests=30, window_seconds=60),
            'hot_pic': RateLimitConfig(max_requests=5, window_seconds=60),
            'api': RateLimitConfig(max_requests=100, window_seconds=60),
        }
    
    async def is_allowed(self, user_id: int, request_type: str = 'message') -> bool:
        """Проверяет, разрешен ли запрос пользователю"""
        now = time.time()
        
        # Проверяем, не заблокирован ли пользователь
        if user_id in self.blocked_users:
            if now - self.blocked_users[user_id] < self.configs[request_type].block_duration:
                return False
            else:
                # Разблокируем пользователя
                del self.blocked_users[user_id]
        
        # Получаем конфигурацию для типа запроса
        config = self.configs.get(request_type, self.configs['message'])
        
        # Очищаем старые запросы
        user_requests = self.user_requests[user_id]
        cutoff_time = now - config.window_seconds
        user_requests[:] = [req_time for req_time in user_requests if req_time > cutoff_time]
        
        # Проверяем лимит
        if len(user_requests) >= config.max_requests:
            # Блокируем пользователя
            self.blocked_users[user_id] = now
            return False
        
        # Добавляем текущий запрос
        user_requests.append(now)
        return True
    
    async def get_remaining_requests(self, user_id: int, request_type: str = 'message') -> int:
        """Возвращает количество оставшихся запросов"""
        now = time.time()
        config = self.configs.get(request_type, self.configs['message'])
        
        user_requests = self.user_requests[user_id]
        cutoff_time = now - config.window_seconds
        user_requests[:] = [req_time for req_time in user_requests if req_time > cutoff_time]
        
        return max(0, config.max_requests - len(user_requests))
    
    async def get_reset_time(self, user_id: int, request_type: str = 'message') -> Optional[float]:
        """Возвращает время сброса лимита"""
        if user_id in self.blocked_users:
            return self.blocked_users[user_id] + self.configs[request_type].block_duration
        
        user_requests = self.user_requests[user_id]
        if not user_requests:
            return None
        
        config = self.configs.get(request_type, self.configs['message'])
        oldest_request = min(user_requests)
        return oldest_request + config.window_seconds
    
    async def cleanup_expired_data(self):
        """Очищает устаревшие данные"""
        now = time.time()
        
        # Очищаем старые запросы
        for user_id in list(self.user_requests.keys()):
            user_requests = self.user_requests[user_id]
            cutoff_time = now - 3600  # Удаляем запросы старше часа
            user_requests[:] = [req_time for req_time in user_requests if req_time > cutoff_time]
            
            if not user_requests:
                del self.user_requests[user_id]
        
        # Очищаем истекшие блокировки
        for user_id in list(self.blocked_users.keys()):
            if now - self.blocked_users[user_id] > 3600:  # Блокировки старше часа
                del self.blocked_users[user_id]
    
    async def get_user_stats(self, user_id: int) -> Dict:
        """Возвращает статистику пользователя"""
        now = time.time()
        
        stats = {
            'is_blocked': user_id in self.blocked_users,
            'block_remaining': 0,
            'requests_by_type': {}
        }
        
        if user_id in self.blocked_users:
            stats['block_remaining'] = max(0, self.blocked_users[user_id] + 300 - now)
        
        for request_type in self.configs:
            remaining = await self.get_remaining_requests(user_id, request_type)
            reset_time = await self.get_reset_time(user_id, request_type)
            
            stats['requests_by_type'][request_type] = {
                'remaining': remaining,
                'reset_time': reset_time,
                'is_limited': remaining == 0
            }
        
        return stats

# Глобальный экземпляр rate limiter
rate_limiter = RateLimiter()

# Фоновая задача для очистки данных
async def cleanup_task():
    """Фоновая задача для очистки устаревших данных"""
    while True:
        try:
            await rate_limiter.cleanup_expired_data()
            await asyncio.sleep(300)  # Очистка каждые 5 минут
        except Exception as e:
            print(f"Ошибка в задаче очистки rate limiter: {e}")
            await asyncio.sleep(60)
