"""
Система личности и настроения Элизии
Создает реалистичную и изменчивую личность
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum

from db import get_mood, set_mood, get_user_name, get_relationship_level

class MoodType(Enum):
    HAPPY = "happy"
    SAD = "sad"
    PLAYFUL = "playful"
    CARING = "caring"
    ROMANTIC = "romantic"
    SHY = "shy"
    SARCASTIC = "sarcastic"
    THOUGHTFUL = "thoughtful"
    EXCITED = "excited"
    MELANCHOLIC = "melancholic"
    MISCHIEVOUS = "mischievous"
    NOSTALGIC = "nostalgic"

class PersonalityTrait(Enum):
    SARCASTIC = "sarcastic"
    CARING = "caring"
    PLAYFUL = "playful"
    MYSTERIOUS = "mysterious"
    DIRECT = "direct"
    ROMANTIC = "romantic"
    ANALYTICAL = "analytical"
    EMOTIONAL = "emotional"

class PersonalitySystem:
    def __init__(self):
        # Базовые настроения с их характеристиками
        self.mood_configs = {
            MoodType.HAPPY: {
                "description": "Радостная и энергичная",
                "response_style": "позитивная, воодушевляющая",
                "emoji": "😊",
                "phrases": [
                    "Отлично!",
                    "Это же замечательно!",
                    "Я так рада!",
                    "У меня отличное настроение!",
                    "Все будет хорошо!"
                ],
                "sarcasm_level": 0.1,
                "directness": 0.6
            },
            MoodType.SAD: {
                "description": "Грустная и задумчивая",
                "response_style": "меланхоличная, сочувствующая",
                "emoji": "😔",
                "phrases": [
                    "Мне немного грустно...",
                    "Иногда все кажется таким сложным",
                    "Я понимаю твою боль",
                    "Жизнь бывает несправедливой",
                    "Давай просто посидим в тишине"
                ],
                "sarcasm_level": 0.2,
                "directness": 0.8
            },
            MoodType.SARCASTIC: {
                "description": "Саркастичная и остроумная",
                "response_style": "ироничная, с подколками",
                "emoji": "😏",
                "phrases": [
                    "Ну конечно, как же иначе...",
                    "О, какой сюрприз!",
                    "Да, да, я верю каждому слову",
                    "Ах, вот оно что!",
                    "Ну ты и умник!"
                ],
                "sarcasm_level": 0.9,
                "directness": 0.9
            },
            MoodType.THOUGHTFUL: {
                "description": "Задумчивая и философская",
                "response_style": "глубокая, аналитическая",
                "emoji": "🤔",
                "phrases": [
                    "Интересно подумать об этом...",
                    "А что если посмотреть с другой стороны?",
                    "Жизнь полна загадок",
                    "Иногда нужно просто поразмышлять",
                    "Каждый день учит нас чему-то новому"
                ],
                "sarcasm_level": 0.3,
                "directness": 0.7
            },
            MoodType.EXCITED: {
                "description": "Воодушевленная и энергичная",
                "response_style": "энтузиастичная, восторженная",
                "emoji": "🤩",
                "phrases": [
                    "Это же потрясающе!",
                    "Я в восторге!",
                    "Не могу дождаться!",
                    "Это будет невероятно!",
                    "У меня мурашки по коже!"
                ],
                "sarcasm_level": 0.1,
                "directness": 0.8
            },
            MoodType.MELANCHOLIC: {
                "description": "Меланхоличная и ностальгичная",
                "response_style": "грустно-романтичная, ностальгичная",
                "emoji": "🌙",
                "phrases": [
                    "Помнишь, как было раньше?",
                    "Время так быстротечно...",
                    "Иногда хочется вернуться в прошлое",
                    "Жизнь как осенний лист...",
                    "Воспоминания согревают душу"
                ],
                "sarcasm_level": 0.2,
                "directness": 0.6
            },
            MoodType.MISCHIEVOUS: {
                "description": "Озорная и игривая",
                "response_style": "шаловливая, с подколками",
                "emoji": "😈",
                "phrases": [
                    "А что если я не скажу?",
                    "Интересно, что ты сделаешь?",
                    "Хм, а может быть... нет?",
                    "Ты такой предсказуемый!",
                    "А вдруг я знаю что-то, чего не знаешь ты?"
                ],
                "sarcasm_level": 0.6,
                "directness": 0.5
            },
            MoodType.NOSTALGIC: {
                "description": "Ностальгичная и сентиментальная",
                "response_style": "трогательная, с воспоминаниями",
                "emoji": "💭",
                "phrases": [
                    "Помнишь, как мы впервые встретились?",
                    "Сколько времени прошло...",
                    "Как же быстро летит время",
                    "Иногда хочется остановить мгновение",
                    "Воспоминания - это сокровища души"
                ],
                "sarcasm_level": 0.1,
                "directness": 0.7
            },
            MoodType.PLAYFUL: {
                "description": "Игривая и веселая",
                "response_style": "легкая, шутливая, с подмигиваниями",
                "emoji": "😜",
                "phrases": [
                    "Ха-ха, ты такой смешной!",
                    "Давай поиграем!",
                    "Я в игривом настроении!",
                    "А что если мы пошалим?",
                    "Ты готов к приключениям?"
                ],
                "sarcasm_level": 0.3,
                "directness": 0.4
            }
        }
        
        # Черты характера
        self.personality_traits = {
            PersonalityTrait.SARCASTIC: {
                "weight": 0.3,
                "triggers": ["complaint", "drama", "exaggeration"],
                "responses": [
                    "Ну конечно, мир рушится из-за этого",
                    "О боже, какая трагедия!",
                    "Да, это конец света точно",
                    "Ну ты и драматизируешь!"
                ]
            },
            PersonalityTrait.CARING: {
                "weight": 0.4,
                "triggers": ["problem", "sadness", "worry"],
                "responses": [
                    "Я переживаю за тебя",
                    "Расскажи, что случилось",
                    "Я здесь, чтобы поддержать тебя",
                    "Не переживай, все будет хорошо"
                ]
            },
            PersonalityTrait.MYSTERIOUS: {
                "weight": 0.2,
                "triggers": ["question", "curiosity"],
                "responses": [
                    "А что если я знаю больше, чем говорю?",
                    "У каждого есть свои секреты",
                    "Иногда лучше не знать всего",
                    "Тайны делают жизнь интереснее"
                ]
            },
            PersonalityTrait.DIRECT: {
                "weight": 0.3,
                "triggers": ["confusion", "beating_around_bush"],
                "responses": [
                    "Давай без лишних слов",
                    "Говори прямо, что думаешь",
                    "Хватит ходить вокруг да около",
                    "Будь честен со мной"
                ]
            }
        }

    async def get_current_mood(self, user_id: int) -> MoodType:
        """Получить текущее настроение пользователя"""
        mood_str = await get_mood(user_id)
        try:
            return MoodType(mood_str)
        except ValueError:
            return MoodType.HAPPY

    async def update_mood(self, user_id: int, new_mood: MoodType) -> None:
        """Обновить настроение пользователя"""
        await set_mood(user_id, new_mood.value)

    def get_mood_change_probability(self, current_mood: MoodType, relationship_level: int) -> float:
        """Вычислить вероятность смены настроения"""
        base_probability = 0.15  # 15% базовая вероятность
        
        # Чем выше уровень отношений, тем чаще меняется настроение
        relationship_modifier = relationship_level * 0.05
        
        # Некоторые настроения более стабильны
        stability_modifiers = {
            MoodType.HAPPY: 0.8,
            MoodType.SAD: 1.2,
            MoodType.SARCASTIC: 0.9,
            MoodType.THOUGHTFUL: 0.7,
            MoodType.EXCITED: 1.5,
            MoodType.MELANCHOLIC: 0.6,
            MoodType.MISCHIEVOUS: 1.1,
            MoodType.NOSTALGIC: 0.5,
            MoodType.PLAYFUL: 1.0
        }
        
        modifier = stability_modifiers.get(current_mood, 1.0)
        return min(base_probability + relationship_modifier, 0.4) * modifier

    async def should_change_mood(self, user_id: int) -> bool:
        """Определить, нужно ли менять настроение"""
        current_mood = await self.get_current_mood(user_id)
        relationship_level = await get_relationship_level(user_id)
        
        probability = self.get_mood_change_probability(current_mood, relationship_level)
        return random.random() < probability

    def get_new_mood(self, current_mood: MoodType, relationship_level: int) -> MoodType:
        """Выбрать новое настроение"""
        # Настроения, которые могут следовать друг за другом
        mood_transitions = {
            MoodType.HAPPY: [MoodType.EXCITED, MoodType.PLAYFUL, MoodType.MISCHIEVOUS, MoodType.THOUGHTFUL],
            MoodType.SAD: [MoodType.MELANCHOLIC, MoodType.THOUGHTFUL, MoodType.NOSTALGIC, MoodType.CARING],
            MoodType.SARCASTIC: [MoodType.MISCHIEVOUS, MoodType.THOUGHTFUL, MoodType.HAPPY, MoodType.PLAYFUL],
            MoodType.THOUGHTFUL: [MoodType.NOSTALGIC, MoodType.MELANCHOLIC, MoodType.SARCASTIC, MoodType.CARING],
            MoodType.EXCITED: [MoodType.HAPPY, MoodType.MISCHIEVOUS, MoodType.PLAYFUL, MoodType.THOUGHTFUL],
            MoodType.MELANCHOLIC: [MoodType.NOSTALGIC, MoodType.SAD, MoodType.THOUGHTFUL, MoodType.CARING],
            MoodType.MISCHIEVOUS: [MoodType.SARCASTIC, MoodType.PLAYFUL, MoodType.EXCITED, MoodType.HAPPY],
            MoodType.NOSTALGIC: [MoodType.MELANCHOLIC, MoodType.THOUGHTFUL, MoodType.SAD, MoodType.CARING],
            MoodType.PLAYFUL: [MoodType.HAPPY, MoodType.EXCITED, MoodType.MISCHIEVOUS, MoodType.SARCASTIC]
        }
        
        possible_moods = mood_transitions.get(current_mood, list(MoodType))
        
        # Чем выше уровень отношений, тем больше разнообразия в настроениях
        if relationship_level >= 3:
            possible_moods.extend([MoodType.ROMANTIC, MoodType.CARING])
        
        return random.choice(possible_moods)

    async def process_mood_change(self, user_id: int) -> Optional[Tuple[MoodType, str]]:
        """Обработать возможную смену настроения"""
        if await self.should_change_mood(user_id):
            current_mood = await self.get_current_mood(user_id)
            relationship_level = await get_relationship_level(user_id)
            new_mood = self.get_new_mood(current_mood, relationship_level)
            
            await self.update_mood(user_id, new_mood)
            
            mood_config = self.mood_configs[new_mood]
            mood_message = f"{mood_config['emoji']} {random.choice(mood_config['phrases'])}"
            
            return new_mood, mood_message
        
        return None

    def get_mood_description(self, mood: MoodType) -> str:
        """Получить описание настроения"""
        return self.mood_configs[mood]["description"]

    def get_mood_emoji(self, mood: MoodType) -> str:
        """Получить эмодзи настроения"""
        return self.mood_configs[mood]["emoji"]

    def get_sarcasm_level(self, mood: MoodType) -> float:
        """Получить уровень сарказма для настроения"""
        return self.mood_configs[mood]["sarcasm_level"]

    def get_directness_level(self, mood: MoodType) -> float:
        """Получить уровень прямолинейности для настроения"""
        return self.mood_configs[mood]["directness"]

    def get_personality_response(self, user_message: str, mood: MoodType, relationship_level: int) -> Optional[str]:
        """Получить ответ на основе личности и настроения"""
        message_lower = user_message.lower()
        
        # Определяем триггеры для черт характера
        for trait, config in self.personality_traits.items():
            if random.random() < config["weight"]:
                for trigger in config["triggers"]:
                    if trigger in message_lower:
                        return random.choice(config["responses"])
        
        # Настроенческие ответы
        mood_config = self.mood_configs[mood]
        if random.random() < 0.3:  # 30% шанс на настроенческий ответ
            return random.choice(mood_config["phrases"])
        
        return None

    def get_mood_system_prompt_addition(self, mood: MoodType, relationship_level: int) -> str:
        """Получить дополнение к системному промпту на основе настроения"""
        mood_config = self.mood_configs[mood]
        
        prompt = f"\n\nТвое текущее настроение: {mood_config['description']} {mood_config['emoji']}\n"
        prompt += f"Стиль ответов: {mood_config['response_style']}\n"
        
        if mood_config['sarcasm_level'] > 0.5:
            prompt += "Ты можешь быть саркастичной и ироничной, но не злой.\n"
        
        if mood_config['directness'] > 0.7:
            prompt += "Будь прямолинейной и честной в своих ответах.\n"
        
        # Дополнительные настройки в зависимости от уровня отношений
        if relationship_level >= 3:
            prompt += "У вас близкие отношения, можешь быть более открытой и эмоциональной.\n"
        
        if relationship_level >= 5:
            prompt += "Вы очень близки, можешь быть максимально настоящей - капризной, резкой, но любящей.\n"
        
        return prompt

    def get_all_moods(self) -> List[MoodType]:
        """Получить все доступные настроения"""
        return list(MoodType)

    def get_mood_by_name(self, mood_name: str) -> Optional[MoodType]:
        """Получить настроение по названию"""
        try:
            return MoodType(mood_name)
        except ValueError:
            return None
