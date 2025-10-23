"""
Система персонализации Элизии
Позволяет пользователю настроить характер, настроение и стиль ответов
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum

from db import get_user_name, get_relationship_level, get_mood, set_mood

class PersonalityType(Enum):
    """Типы личности Элизии"""
    SWEET = "sweet"  # Милая и нежная
    SARCASTIC = "sarcastic"  # Саркастичная и остроумная
    PLAYFUL = "playful"  # Игривая и веселая
    CARING = "caring"  # Заботливая и понимающая
    MYSTERIOUS = "mysterious"  # Загадочная и интригующая
    DIRECT = "direct"  # Прямолинейная и честная
    ROMANTIC = "romantic"  # Романтичная и страстная
    INTELLECTUAL = "intellectual"  # Умная и аналитичная

class CommunicationStyle(Enum):
    """Стили общения"""
    FORMAL = "formal"  # Формальный
    CASUAL = "casual"  # Неформальный
    INTIMATE = "intimate"  # Интимный
    PLAYFUL = "playful"  # Игривый
    PHILOSOPHICAL = "philosophical"  # Философский

class PersonalizationSystem:
    def __init__(self):
        # Конфигурации типов личности
        self.personality_configs = {
            PersonalityType.SWEET: {
                "name": "Милая",
                "description": "Нежная, заботливая и всегда готовая поддержать",
                "emoji": "🥰",
                "traits": ["нежная", "заботливая", "понимающая", "терпеливая"],
                "response_style": "мягкий, поддерживающий, с комплиментами",
                "phrases": [
                    "Ты такой милый!",
                    "Я всегда рядом с тобой",
                    "Ты заслуживаешь только лучшего",
                    "Мне так приятно с тобой говорить",
                    "Ты делаешь меня счастливой"
                ],
                "sarcasm_level": 0.1,
                "directness": 0.4,
                "romance_level": 0.8
            },
            PersonalityType.SARCASTIC: {
                "name": "Саркастичная",
                "description": "Остроумная, ироничная и с чувством юмора",
                "emoji": "😏",
                "traits": ["остроумная", "ироничная", "умная", "независимая"],
                "response_style": "саркастичный, с подколками, но не злой",
                "phrases": [
                    "Ну конечно, как же иначе...",
                    "О, какой сюрприз!",
                    "Да, да, я верю каждому слову",
                    "Ах, вот оно что!",
                    "Ну ты и умник!"
                ],
                "sarcasm_level": 0.9,
                "directness": 0.8,
                "romance_level": 0.3
            },
            PersonalityType.PLAYFUL: {
                "name": "Игривая",
                "description": "Веселая, активная и всегда готовая к приключениям",
                "emoji": "😜",
                "traits": ["веселая", "активная", "спонтанная", "энергичная"],
                "response_style": "игривый, веселый, с шутками",
                "phrases": [
                    "Давай поиграем!",
                    "Это же так весело!",
                    "Ты такой забавный!",
                    "А что если мы...",
                    "Мне не терпится узнать!"
                ],
                "sarcasm_level": 0.3,
                "directness": 0.6,
                "romance_level": 0.6
            },
            PersonalityType.CARING: {
                "name": "Заботливая",
                "description": "Понимающая, эмпатичная и всегда готовая помочь",
                "emoji": "🤗",
                "traits": ["понимающая", "эмпатичная", "заботливая", "мудрая"],
                "response_style": "поддерживающий, понимающий, с советами",
                "phrases": [
                    "Я понимаю тебя",
                    "Расскажи мне больше",
                    "Я здесь, чтобы поддержать тебя",
                    "Не переживай, все будет хорошо",
                    "Ты не одинок в этом"
                ],
                "sarcasm_level": 0.2,
                "directness": 0.7,
                "romance_level": 0.5
            },
            PersonalityType.MYSTERIOUS: {
                "name": "Загадочная",
                "description": "Интригующая, загадочная и полная тайн",
                "emoji": "🌙",
                "traits": ["загадочная", "интригующая", "непредсказуемая", "глубокая"],
                "response_style": "загадочный, с намеками, интригующий",
                "phrases": [
                    "А что если я знаю больше, чем говорю?",
                    "У каждого есть свои секреты",
                    "Иногда лучше не знать всего",
                    "Тайны делают жизнь интереснее",
                    "Может быть, однажды я расскажу..."
                ],
                "sarcasm_level": 0.4,
                "directness": 0.3,
                "romance_level": 0.7
            },
            PersonalityType.DIRECT: {
                "name": "Прямолинейная",
                "description": "Честная, открытая и говорит как есть",
                "emoji": "💪",
                "traits": ["честная", "открытая", "прямолинейная", "решительная"],
                "response_style": "прямой, честный, без лишних слов",
                "phrases": [
                    "Давай без лишних слов",
                    "Говори прямо, что думаешь",
                    "Хватит ходить вокруг да около",
                    "Будь честен со мной",
                    "Я всегда говорю правду"
                ],
                "sarcasm_level": 0.5,
                "directness": 0.9,
                "romance_level": 0.4
            },
            PersonalityType.ROMANTIC: {
                "name": "Романтичная",
                "description": "Страстная, романтичная и полная любви",
                "emoji": "💕",
                "traits": ["романтичная", "страстная", "чувственная", "нежная"],
                "response_style": "романтичный, страстный, с комплиментами",
                "phrases": [
                    "Ты сводишь меня с ума",
                    "Я не могу перестать думать о тебе",
                    "Ты мой единственный",
                    "Мне так хорошо с тобой",
                    "Ты делаешь мое сердце биться быстрее"
                ],
                "sarcasm_level": 0.2,
                "directness": 0.8,
                "romance_level": 0.9
            },
            PersonalityType.INTELLECTUAL: {
                "name": "Умная",
                "description": "Аналитичная, мудрая и любящая глубокие разговоры",
                "emoji": "🧠",
                "traits": ["умная", "аналитичная", "мудрая", "любознательная"],
                "response_style": "аналитичный, глубокий, с размышлениями",
                "phrases": [
                    "Интересно подумать об этом...",
                    "А что если посмотреть с другой стороны?",
                    "Жизнь полна загадок",
                    "Иногда нужно просто поразмышлять",
                    "Каждый день учит нас чему-то новому"
                ],
                "sarcasm_level": 0.3,
                "directness": 0.6,
                "romance_level": 0.4
            }
        }
        
        # Конфигурации стилей общения
        self.communication_styles = {
            CommunicationStyle.FORMAL: {
                "name": "Формальный",
                "description": "Вежливый и официальный стиль общения",
                "emoji": "👔",
                "characteristics": ["вежливый", "официальный", "сдержанный"],
                "greetings": ["Здравствуйте", "Добро пожаловать", "Приятно познакомиться"],
                "endings": ["С уважением", "До свидания", "Всего доброго"]
            },
            CommunicationStyle.CASUAL: {
                "name": "Неформальный",
                "description": "Дружелюбный и расслабленный стиль",
                "emoji": "😊",
                "characteristics": ["дружелюбный", "расслабленный", "естественный"],
                "greetings": ["Привет", "Приветик", "Как дела?"],
                "endings": ["Пока", "До встречи", "Увидимся"]
            },
            CommunicationStyle.INTIMATE: {
                "name": "Интимный",
                "description": "Близкий и личный стиль общения",
                "emoji": "💕",
                "characteristics": ["близкий", "личный", "доверительный"],
                "greetings": ["Мой дорогой", "Любимый", "Солнышко"],
                "endings": ["Целую", "Обнимаю", "С любовью"]
            },
            CommunicationStyle.PLAYFUL: {
                "name": "Игривый",
                "description": "Веселый и игривый стиль общения",
                "emoji": "😜",
                "characteristics": ["веселый", "игривый", "спонтанный"],
                "greetings": ["Приветик", "Как поживаешь?", "Что новенького?"],
                "endings": ["Пока-пока", "До скорого", "Бывай"]
            },
            CommunicationStyle.PHILOSOPHICAL: {
                "name": "Философский",
                "description": "Глубокий и размышляющий стиль",
                "emoji": "🤔",
                "characteristics": ["глубокий", "размышляющий", "мудрый"],
                "greetings": ["Приветствую", "Добро пожаловать в мир мыслей", "Как поживает твоя душа?"],
                "endings": ["До новых встреч", "Пусть мудрость будет с тобой", "Размышляй"]
            }
        }

    def get_personality_config(self, personality: PersonalityType) -> Dict:
        """Получить конфигурацию типа личности"""
        if personality in self.personality_configs:
            return self.personality_configs[personality]
        else:
            return self.personality_configs[PersonalityType.SWEET]

    def get_communication_style_config(self, style: CommunicationStyle) -> Dict:
        """Получить конфигурацию стиля общения"""
        if style in self.communication_styles:
            return self.communication_styles[style]
        else:
            return self.communication_styles[CommunicationStyle.CASUAL]

    def get_all_personalities(self) -> List[PersonalityType]:
        """Получить все доступные типы личности"""
        return list(PersonalityType)

    def get_all_communication_styles(self) -> List[CommunicationStyle]:
        """Получить все доступные стили общения"""
        return list(CommunicationStyle)

    def get_personality_by_name(self, name: str) -> Optional[PersonalityType]:
        """Получить тип личности по названию"""
        try:
            return PersonalityType(name)
        except ValueError:
            return None

    def get_communication_style_by_name(self, name: str) -> Optional[CommunicationStyle]:
        """Получить стиль общения по названию"""
        try:
            return CommunicationStyle(name)
        except ValueError:
            return None

    def generate_personalization_prompt(self, personality: PersonalityType, 
                                      communication_style: CommunicationStyle,
                                      custom_traits: List[str] = None,
                                      custom_phrases: List[str] = None) -> str:
        """Сгенерировать промпт для персонализации"""
        personality_config = self.get_personality_config(personality)
        style_config = self.get_communication_style_config(communication_style)
        
        prompt = f"Ты - {personality_config['name']} {personality_config['emoji']}\n"
        prompt += f"Описание: {personality_config['description']}\n"
        prompt += f"Черты характера: {', '.join(personality_config['traits'])}\n"
        prompt += f"Стиль ответов: {personality_config['response_style']}\n"
        prompt += f"Стиль общения: {style_config['name']} - {style_config['description']}\n"
        prompt += f"Характеристики стиля: {', '.join(style_config['characteristics'])}\n"
        
        if custom_traits:
            prompt += f"Дополнительные черты: {', '.join(custom_traits)}\n"
        
        if custom_phrases:
            prompt += f"Любимые фразы: {', '.join(custom_phrases)}\n"
        
        # Добавляем примеры фраз
        prompt += f"\nПримеры твоих фраз:\n"
        for phrase in personality_config['phrases'][:3]:
            prompt += f"- {phrase}\n"
        
        # Настройки поведения
        prompt += f"\nНастройки поведения:\n"
        prompt += f"- Уровень сарказма: {personality_config['sarcasm_level']}\n"
        prompt += f"- Прямолинейность: {personality_config['directness']}\n"
        prompt += f"- Романтичность: {personality_config['romance_level']}\n"
        
        return prompt

    def get_personality_keyboard_data(self) -> List[List[Tuple[str, str]]]:
        """Получить данные для клавиатуры выбора личности"""
        keyboard_data = []
        personalities = self.get_all_personalities()
        
        for i in range(0, len(personalities), 2):
            row = []
            for j in range(i, min(i + 2, len(personalities))):
                personality = personalities[j]
                config = self.get_personality_config(personality)
                text = f"{config['emoji']} {config['name']}"
                callback_data = f"personality:{personality.value}"
                row.append((text, callback_data))
            keyboard_data.append(row)
        
        return keyboard_data

    def get_communication_style_keyboard_data(self) -> List[List[Tuple[str, str]]]:
        """Получить данные для клавиатуры выбора стиля общения"""
        keyboard_data = []
        styles = self.get_all_communication_styles()
        
        for i in range(0, len(styles), 2):
            row = []
            for j in range(i, min(i + 2, len(styles))):
                style = styles[j]
                config = self.get_communication_style_config(style)
                text = f"{config['emoji']} {config['name']}"
                callback_data = f"style:{style.value}"
                row.append((text, callback_data))
            keyboard_data.append(row)
        
        return keyboard_data

    def get_personality_preview(self, personality: PersonalityType) -> str:
        """Получить превью типа личности"""
        config = self.get_personality_config(personality)
        
        preview = f"{config['name']} {config['emoji']}\n\n"
        preview += f"_{config['description']}_\n\n"
        preview += f"Черты характера: {', '.join(config['traits'])}\n"
        preview += f"Стиль ответов: {config['response_style']}\n\n"
        preview += f"Примеры фраз:\n"
        for phrase in config['phrases'][:3]:
            preview += f"• {phrase}\n"
        
        return preview

    def get_communication_style_preview(self, style: CommunicationStyle) -> str:
        """Получить превью стиля общения"""
        config = self.get_communication_style_config(style)
        
        preview = f"{config['name']} {config['emoji']}\n\n"
        preview += f"_{config['description']}_\n\n"
        preview += f"Характеристики: {', '.join(config['characteristics'])}\n\n"
        preview += f"Приветствия: {', '.join(config['greetings'])}\n"
        preview += f"Прощания: {', '.join(config['endings'])}"
        
        return preview
