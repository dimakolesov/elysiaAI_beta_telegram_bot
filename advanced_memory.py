"""
Продвинутая система памяти и контекста
Запоминает факты о пользователе и поддерживает контекст разговора
"""

import re
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict

from db import (
    get_memory, save_message, get_user_name, get_relationship_level,
    get_total_messages, get_days_active
)

@dataclass
class UserFact:
    """Факт о пользователе"""
    fact_type: str  # "job", "pet", "hobby", "location", "family", "goal", "fear", "dream"
    fact_content: str
    confidence: float  # 0.0 - 1.0
    first_mentioned: datetime
    last_mentioned: datetime
    mention_count: int

@dataclass
class ConversationTopic:
    """Тема разговора"""
    topic: str
    first_discussed: datetime
    last_discussed: datetime
    discussion_count: int
    sentiment: str  # "positive", "negative", "neutral"

class AdvancedMemorySystem:
    def __init__(self):
        # Паттерны для извлечения фактов
        self.fact_patterns = {
            "job": [
                r"работаю\s+(?:как\s+)?([^,\.!?]+)",
                r"я\s+([^,\.!?]*программист[^,\.!?]*)",
                r"моя\s+работа\s+([^,\.!?]+)",
                r"занимаюсь\s+([^,\.!?]+)",
                r"по\s+профессии\s+([^,\.!?]+)"
            ],
            "pet": [
                r"у\s+меня\s+(?:есть\s+)?([^,\.!?]*собак[аиы]?[^,\.!?]*)",
                r"моя\s+([^,\.!?]*собак[аиы]?[^,\.!?]*)",
                r"у\s+меня\s+(?:есть\s+)?([^,\.!?]*кот[аиы]?[^,\.!?]*)",
                r"моя\s+([^,\.!?]*кот[аиы]?[^,\.!?]*)",
                r"животное\s+([^,\.!?]+)",
                r"питомец\s+([^,\.!?]+)"
            ],
            "hobby": [
                r"увлекаюсь\s+([^,\.!?]+)",
                r"мое\s+хобби\s+([^,\.!?]+)",
                r"люблю\s+([^,\.!?]+)",
                r"занимаюсь\s+([^,\.!?]+)",
                r"в\s+свободное\s+время\s+([^,\.!?]+)"
            ],
            "location": [
                r"живу\s+в\s+([^,\.!?]+)",
                r"из\s+([^,\.!?]+)",
                r"нахожусь\s+в\s+([^,\.!?]+)",
                r"город\s+([^,\.!?]+)",
                r"страна\s+([^,\.!?]+)"
            ],
            "family": [
                r"у\s+меня\s+(?:есть\s+)?([^,\.!?]*семья[^,\.!?]*)",
                r"моя\s+([^,\.!?]*семья[^,\.!?]*)",
                r"родители\s+([^,\.!?]+)",
                r"мама\s+([^,\.!?]+)",
                r"папа\s+([^,\.!?]+)",
                r"брат\s+([^,\.!?]+)",
                r"сестра\s+([^,\.!?]+)"
            ],
            "goal": [
                r"хочу\s+([^,\.!?]+)",
                r"мечтаю\s+([^,\.!?]+)",
                r"планирую\s+([^,\.!?]+)",
                r"цель\s+([^,\.!?]+)",
                r"стремлюсь\s+([^,\.!?]+)"
            ],
            "fear": [
                r"боюсь\s+([^,\.!?]+)",
                r"страх\s+([^,\.!?]+)",
                r"переживаю\s+([^,\.!?]+)",
                r"волнуюсь\s+([^,\.!?]+)"
            ],
            "dream": [
                r"мечта\s+([^,\.!?]+)",
                r"хотел\s+бы\s+([^,\.!?]+)",
                r"представляю\s+([^,\.!?]+)"
            ]
        }
        
        # Ключевые слова для определения тем разговора
        self.topic_keywords = {
            "работа": ["работа", "карьера", "профессия", "офис", "коллеги", "начальник", "проект"],
            "отношения": ["любовь", "встречаюсь", "парень", "девушка", "семья", "брак", "развод"],
            "здоровье": ["здоровье", "болезнь", "врач", "больница", "лекарство", "спорт", "диета"],
            "путешествия": ["путешествие", "отпуск", "поездка", "страна", "город", "отель", "самолет"],
            "учеба": ["учеба", "университет", "школа", "экзамен", "диплом", "студент", "преподаватель"],
            "хобби": ["хобби", "увлечение", "спорт", "музыка", "кино", "книги", "игры"],
            "проблемы": ["проблема", "трудность", "сложно", "не получается", "не знаю", "помогите"],
            "планы": ["план", "будущее", "цель", "мечта", "хочу", "собираюсь", "надеюсь"]
        }

    async def extract_facts(self, user_id: int, message: str) -> List[UserFact]:
        """Извлечь факты из сообщения пользователя"""
        facts = []
        message_lower = message.lower()
        
        for fact_type, patterns in self.fact_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, message_lower, re.IGNORECASE)
                for match in matches:
                    if len(match.strip()) > 2:  # Игнорируем слишком короткие совпадения
                        fact = UserFact(
                            fact_type=fact_type,
                            fact_content=match.strip(),
                            confidence=0.8,  # Базовая уверенность
                            first_mentioned=datetime.now(),
                            last_mentioned=datetime.now(),
                            mention_count=1
                        )
                        facts.append(fact)
        
        return facts

    async def get_user_facts(self, user_id: int) -> Dict[str, List[UserFact]]:
        """Получить все факты о пользователе"""
        # В реальной реализации здесь был бы запрос к БД
        # Пока возвращаем пустой словарь
        return {}

    async def save_user_fact(self, user_id: int, fact: UserFact) -> None:
        """Сохранить факт о пользователе"""
        # В реальной реализации здесь был бы запрос к БД
        pass

    async def get_conversation_topics(self, user_id: int) -> List[ConversationTopic]:
        """Получить темы разговоров с пользователем"""
        # В реальной реализации здесь был бы запрос к БД
        return []

    async def identify_topic(self, message: str) -> Optional[str]:
        """Определить тему разговора"""
        message_lower = message.lower()
        
        for topic, keywords in self.topic_keywords.items():
            for keyword in keywords:
                if keyword in message_lower:
                    return topic
        
        return None

    async def get_memory_context(self, user_id: int, limit: int = 10) -> str:
        """Получить контекст памяти для разговора"""
        # Получаем последние сообщения
        memory_pairs = await get_memory(user_id, limit)
        context_parts = []
        
        # Добавляем базовую информацию о пользователе
        user_name = await get_user_name(user_id)
        if user_name:
            context_parts.append(f"Пользователя зовут {user_name}")
        
        # Добавляем информацию об отношениях
        relationship_level = await get_relationship_level(user_id)
        if relationship_level > 1:
            context_parts.append(f"Уровень отношений: {relationship_level}/5")
        
        # Добавляем статистику
        total_messages = await get_total_messages(user_id)
        days_active = await get_days_active(user_id)
        context_parts.append(f"Пользователь написал {total_messages} сообщений за {days_active} дней")
        
        # Добавляем последние сообщения
        if memory_pairs:
            context_parts.append("Последние сообщения:")
            for message, role in memory_pairs[-5:]:  # Последние 5 сообщений
                role_name = "Пользователь" if role == "user" else "Подруга"
                context_parts.append(f"{role_name}: {message[:100]}...")
        
        return "\n".join(context_parts)

    async def get_personalized_greeting(self, user_id: int) -> str:
        """Получить персонализированное приветствие"""
        user_name = await get_user_name(user_id)
        days_active = await get_days_active(user_id)
        relationship_level = await get_relationship_level(user_id)
        
        greetings = []
        
        if user_name:
            greetings.append(f"Привет, {user_name}!")
        else:
            greetings.append("Привет!")
        
        # Добавляем персонализацию в зависимости от уровня отношений
        if relationship_level >= 3:
            greetings.append("Как дела, дорогой?")
        elif relationship_level >= 2:
            greetings.append("Рада тебя видеть!")
        else:
            greetings.append("Как поживаешь?")
        
        # Добавляем информацию о времени активности
        if days_active > 0:
            if days_active == 1:
                greetings.append("Это твой первый день со мной!")
            elif days_active < 7:
                greetings.append(f"Мы общаемся уже {days_active} дней!")
            elif days_active < 30:
                greetings.append(f"Уже {days_active} дней вместе!")
            else:
                greetings.append(f"Целых {days_active} дней знакомства!")
        
        return " ".join(greetings)

    async def get_contextual_response(self, user_id: int, user_message: str) -> Optional[str]:
        """Получить контекстуальный ответ на основе памяти"""
        message_lower = user_message.lower()
        
        # Проверяем на упоминание прошлых тем
        if any(word in message_lower for word in ["помнишь", "в прошлый раз", "как я говорил", "как ты говорила"]):
            return "Конечно помню! Расскажи подробнее, что изменилось?"
        
        # Проверяем на вопросы о прошлом
        if any(word in message_lower for word in ["как дела с", "что с", "как прошло", "как было"]):
            return "Хорошо, что ты спрашиваешь! Давай обсудим это подробнее."
        
        # Проверяем на повторение темы
        topic = await self.identify_topic(user_message)
        if topic:
            return f"Ах, снова про {topic}? Интересно, что изменилось с прошлого раза!"
        
        return None

    async def update_memory_context(self, user_id: int, user_message: str, bot_response: str) -> None:
        """Обновить контекст памяти после разговора"""
        # Извлекаем факты из сообщения пользователя
        facts = await self.extract_facts(user_id, user_message)
        for fact in facts:
            await self.save_user_fact(user_id, fact)
        
        # Определяем тему разговора
        topic = await self.identify_topic(user_message)
        if topic:
            # В реальной реализации здесь было бы сохранение темы
            pass

    def format_facts_for_prompt(self, facts: Dict[str, List[UserFact]]) -> str:
        """Форматировать факты для системного промпта"""
        if not facts:
            return ""
        
        context_parts = ["Известные факты о пользователе:"]
        
        for fact_type, fact_list in facts.items():
            if fact_list:
                type_names = {
                    "job": "Работа",
                    "pet": "Питомцы",
                    "hobby": "Хобби",
                    "location": "Местоположение",
                    "family": "Семья",
                    "goal": "Цели",
                    "fear": "Страхи",
                    "dream": "Мечты"
                }
                
                type_name = type_names.get(fact_type, fact_type)
                context_parts.append(f"{type_name}:")
                
                for fact in fact_list:
                    context_parts.append(f"- {fact.fact_content}")
        
        return "\n".join(context_parts)

    async def get_memory_summary(self, user_id: int) -> str:
        """Получить краткое резюме памяти о пользователе"""
        user_name = await get_user_name(user_id)
        relationship_level = await get_relationship_level(user_id)
        total_messages = await get_total_messages(user_id)
        days_active = await get_days_active(user_id)
        
        summary_parts = []
        
        if user_name:
            summary_parts.append(f"Пользователь: {user_name}")
        
        summary_parts.append(f"Уровень отношений: {relationship_level}/5")
        summary_parts.append(f"Активность: {total_messages} сообщений за {days_active} дней")
        
        # Добавляем оценку отношений
        if relationship_level >= 4:
            summary_parts.append("Очень близкие отношения")
        elif relationship_level >= 3:
            summary_parts.append("Близкие отношения")
        elif relationship_level >= 2:
            summary_parts.append("Дружеские отношения")
        else:
            summary_parts.append("Знакомство")
        
        return "\n".join(summary_parts)
