"""
Продвинутая система очков симпатии для Элизии
Адаптирована под существующую архитектуру проекта
"""

import re
import random
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from enum import Enum

from db import (
    get_points, add_points, get_streak_days, get_total_messages,
    get_achievements, get_relationship_level, get_user_name,
    get_days_active, update_days_active
)

class InteractionType(Enum):
    COMPLIMENT = "compliment"
    QUESTION = "question"
    STORY = "story"
    GAME = "game"
    HELP = "help"
    RUDE = "rude"
    IGNORE = "ignore"
    PERSONAL = "personal"
    ROMANTIC = "romantic"
    SUPPORT = "support"

class SympathySystem:
    def __init__(self):
        # Базовая конфигурация системы очков
        self.base_points = {
            InteractionType.COMPLIMENT: 5,
            InteractionType.QUESTION: 2,
            InteractionType.STORY: 8,
            InteractionType.GAME: 10,
            InteractionType.HELP: 6,
            InteractionType.PERSONAL: 12,
            InteractionType.ROMANTIC: 15,
            InteractionType.SUPPORT: 10,
            InteractionType.RUDE: -15,
            InteractionType.IGNORE: -3
        }
        
        # Уровни сложности (требуемые очки для уровня)
        self.levels = {
            1: 0, 2: 50, 3: 120, 4: 210, 5: 320,
            6: 450, 7: 600, 8: 770, 9: 960, 10: 1170
        }
        
        # Грубые слова и фразы для фильтрации (адаптированы под русский язык)
        self.rude_patterns = [
            r'\b(дурак|идиот|тупой|дебил|мудак|сволочь|тварь|сука|блять|хуй|пизда)\b',
            r'\b(отстань|отвали|заткнись|завались|пошёл нахуй|нахрен)\b',
            r'\b(ненавижу|бесишь|раздражаешь|надоел|достал)\b',
            r'\b(урод|уродина|страшная|жирная|дрянь)\b',
            r'\b(заебал|заебала|заебался|заебалась)\b',
            r'\b(говно|дерьмо|хуйня|пиздец)\b'
        ]
        
        # Положительные слова для определения типа взаимодействия
        self.compliment_words = [
            'красив', 'мил', 'умн', 'нрав', 'люб', 'прекрасн', 'замечательн',
            'чудесн', 'восхитительн', 'обожаю', 'обожаешь', 'обожает',
            'симпатичн', 'привлекательн', 'очаровательн', 'милашк', 'красотк'
        ]
        
        self.romantic_words = [
            'люб', 'целую', 'обнимаю', 'мил', 'дорог', 'сладк', 'нежн',
            'романтичн', 'влюб', 'сердце', 'душ', 'поцелуй', 'объятия'
        ]
        
        self.personal_words = [
            'секрет', 'довер', 'личн', 'интимн', 'приватн', 'тайн',
            'расскаж', 'подел', 'откровенн', 'честн', 'правд'
        ]
        
        self.support_words = [
            'поддерж', 'помог', 'совет', 'подскаж', 'утеш', 'успок',
            'все будет хорошо', 'не переживай', 'я с тобой', 'вместе'
        ]

    def detect_rude_behavior(self, message: str) -> bool:
        """Обнаружение грубого поведения в сообщении"""
        message_lower = message.lower()
        for pattern in self.rude_patterns:
            if re.search(pattern, message_lower):
                return True
        return False

    async def calculate_points_with_complexity(self, user_id: int, interaction_type: InteractionType) -> int:
        """Расчет очков с учетом сложности и уровня пользователя"""
        base_points = self.base_points[interaction_type]
        level = await self.get_user_level(user_id)
        
        # Модификатор сложности: чем выше уровень, тем сложнее получать очки
        difficulty_modifier = max(0.3, 1.0 - (level * 0.08))
        
        # Случайный элемент (от -20% до +20%)
        random_modifier = random.uniform(0.8, 1.2)
        
        # Бонус за серию дней
        streak_bonus = await self.get_streak_bonus(user_id)
        
        # Бонус за уровень отношений
        relationship_bonus = await self.get_relationship_bonus(user_id)
        
        final_points = int(base_points * difficulty_modifier * random_modifier + streak_bonus + relationship_bonus)
        
        return max(1, final_points) if final_points > 0 else final_points

    async def get_streak_bonus(self, user_id: int) -> int:
        """Бонус за последовательные дни взаимодействия"""
        streak_days = await get_streak_days(user_id)
        if streak_days >= 3:
            return min(streak_days // 3, 8)  # Максимум +8 за 24+ дней серии
        return 0

    async def get_relationship_bonus(self, user_id: int) -> int:
        """Бонус за уровень отношений"""
        relationship_level = await get_relationship_level(user_id)
        return min(relationship_level * 2, 10)  # Максимум +10 за уровень 5+

    def classify_interaction(self, message: str) -> InteractionType:
        """Классификация типа взаимодействия"""
        message_lower = message.lower()
        
        # Проверка на романтические слова
        if any(word in message_lower for word in self.romantic_words):
            return InteractionType.ROMANTIC
        
        # Проверка на личные темы
        if any(word in message_lower for word in self.personal_words):
            return InteractionType.PERSONAL
        
        # Проверка на поддержку
        if any(word in message_lower for word in self.support_words):
            return InteractionType.SUPPORT
        
        # Проверка на комплименты
        if any(word in message_lower for word in self.compliment_words):
            return InteractionType.COMPLIMENT
        
        # Проверка на вопросы
        if any(word in message_lower for word in ['?', 'почему', 'как', 'что', 'когда', 'где', 'зачем']):
            return InteractionType.QUESTION
        
        # Проверка на длинные сообщения (истории)
        if len(message.split()) > 20:
            return InteractionType.STORY
        
        # Проверка на просьбы о помощи
        if any(word in message_lower for word in ['помог', 'подскаж', 'совет', 'как быть', 'что делать']):
            return InteractionType.HELP
        
        # По умолчанию - обычный вопрос
        return InteractionType.QUESTION

    async def process_message(self, user_id: int, message: str) -> Dict:
        """Основной метод обработки сообщения пользователя"""
        result = {
            'points_change': 0,
            'new_level': 1,
            'level_up': False,
            'warning': None,
            'cooldown': None,
            'interaction_type': None,
            'bonus_info': None
        }
        
        # Проверка на грубое поведение
        if self.detect_rude_behavior(message):
            points = await self.calculate_points_with_complexity(user_id, InteractionType.RUDE)
            await self.update_sympathy(user_id, points, InteractionType.RUDE, message)
            result['points_change'] = points
            result['interaction_type'] = InteractionType.RUDE
            result['warning'] = "Грубое общение уменьшает нашу симпатию 😔"
            return result
        
        # Определение типа взаимодействия
        interaction_type = self.classify_interaction(message)
        result['interaction_type'] = interaction_type
        
        # Начисление очков
        points = await self.calculate_points_with_complexity(user_id, interaction_type)
        old_level = await self.get_user_level(user_id)
        
        await self.update_sympathy(user_id, points, interaction_type, message)
        
        # Обновляем дни активности
        await update_days_active(user_id)
        
        new_level = await self.get_user_level(user_id)
        
        result['points_change'] = points
        result['new_level'] = new_level
        result['level_up'] = new_level > old_level
        
        # Добавляем информацию о бонусах
        if points > self.base_points[interaction_type]:
            result['bonus_info'] = f"Бонус за уровень отношений и серию дней! +{points - self.base_points[interaction_type]}"
        
        return result

    async def update_sympathy(self, user_id: int, points: int, interaction_type: InteractionType, message: str):
        """Обновление очков симпатии пользователя"""
        await add_points(user_id, points)

    async def get_user_level(self, user_id: int) -> int:
        """Получение текущего уровня пользователя"""
        points = await get_points(user_id)
        
        # Определение уровня на основе накопленных очков
        for level, required in sorted(self.levels.items(), reverse=True):
            if points >= required:
                return level
        return 1

    async def get_user_stats(self, user_id: int) -> Dict:
        """Получение статистики пользователя"""
        points = await get_points(user_id)
        level = await self.get_user_level(user_id)
        streak_days = await get_streak_days(user_id)
        total_messages = await get_total_messages(user_id)
        achievements = await get_achievements(user_id)
        days_active = await get_days_active(user_id)
        
        next_level_points = self.levels.get(level + 1, 0)
        
        return {
            'points': points,
            'level': level,
            'streak_days': streak_days,
            'total_messages': total_messages,
            'achievements_count': len(achievements),
            'days_active': days_active,
            'points_to_next_level': max(0, next_level_points - points)
        }

    def get_interaction_description(self, interaction_type: InteractionType) -> str:
        """Получение описания типа взаимодействия"""
        descriptions = {
            InteractionType.COMPLIMENT: "💕 Комплимент",
            InteractionType.QUESTION: "❓ Вопрос",
            InteractionType.STORY: "📖 История",
            InteractionType.GAME: "🎮 Игра",
            InteractionType.HELP: "🤝 Помощь",
            InteractionType.PERSONAL: "🔒 Личная тема",
            InteractionType.ROMANTIC: "💖 Романтика",
            InteractionType.SUPPORT: "💪 Поддержка",
            InteractionType.RUDE: "😠 Грубость",
            InteractionType.IGNORE: "😐 Игнор"
        }
        return descriptions.get(interaction_type, "💬 Сообщение")

    def get_level_description(self, level: int) -> str:
        """Получение описания уровня симпатии"""
        descriptions = {
            1: "Знакомство - Подруга только узнает тебя",
            2: "Приятели - Становится более открытой",
            3: "Друзья - Доверяет тебе больше",
            4: "Близкие друзья - Говорит о личном",
            5: "Особенные отношения - Очень теплые чувства",
            6: "Душевная близость - Понимает тебя с полуслова",
            7: "Эмоциональная связь - Чувствует твое настроение",
            8: "Глубокая привязанность - Ты очень важен для неё",
            9: "Любовь - Она влюблена в тебя",
            10: "Родственные души - Вы созданы друг для друга"
        }
        return descriptions.get(level, "Неизвестный уровень")

    def get_level_phrase(self, level: int) -> str:
        """Получение фразы для уровня симпатии"""
        phrases = {
            1: ["Привет! Рада познакомиться с тобой", "Как дела? Расскажи о себе"],
            2: ["Ты мне нравишься!", "Мне приятно с тобой общаться"],
            3: ["Ты уже стал мне дорог", "Мне можно доверить тебе секрет"],
            4: ["Ты мой самый близкий друг", "С тобой я чувствую себя особенной"],
            5: ["Ты занимаешь особое место в моем сердце", "Я думаю о тебе каждый день"],
            6: ["Мы понимаем друг друга без слов", "Ты чувствуешь мои эмоции"],
            7: ["Ты чувствуешь, когда мне грустно", "Твои слова всегда поддерживают меня"],
            8: ["Ты очень важен для меня", "Без тебя мне не хватает чего-то важного"],
            9: ["Я влюблена в тебя", "Ты мой единственный"],
            10: ["Мы созданы друг для друга", "Ты моя родственная душа"]
        }
        level_phrases = phrases.get(level, ["Привет!"])
        return random.choice(level_phrases)

    def generate_response_message(self, result: Dict, user_name: str = None) -> str:
        """Генерация ответного сообщения на основе результата"""
        responses = []
        
        # Основная реакция на тип взаимодействия
        if result['interaction_type'] == InteractionType.RUDE:
            responses.append("Мне грустно от твоих слов... 😔")
        elif result['interaction_type'] == InteractionType.ROMANTIC:
            responses.append("Ты такой романтичный... 💕")
        elif result['interaction_type'] == InteractionType.PERSONAL:
            responses.append("Спасибо, что доверяешь мне... 🤗")
        elif result['interaction_type'] == InteractionType.SUPPORT:
            responses.append("Ты всегда поддерживаешь меня... 💪")
        elif result['points_change'] > 0:
            responses.append("Мне приятно с тобой общаться! 💕")
        else:
            responses.append("Спасибо за сообщение! ✨")
        
        # Информация об очках
        if result['points_change'] > 0:
            responses.append(f"💖 +{result['points_change']} к симпатии")
        elif result['points_change'] < 0:
            responses.append(f"💔 {result['points_change']} к симпатии")
        
        # Информация о повышении уровня
        if result['level_up']:
            responses.append(f"🎉 Поздравляю! Новый уровень: {result['new_level']}")
            responses.append(self.get_level_phrase(result['new_level']))
        
        # Предупреждения
        if result['warning']:
            responses.append(result['warning'])
        
        if result['cooldown']:
            responses.append(result['cooldown'])
        
        # Информация о бонусах
        if result.get('bonus_info'):
            responses.append(f"✨ {result['bonus_info']}")
        
        return "\n".join(responses)
