"""
Система мультиязычности для бота
"""

from typing import Dict, Any
from enum import Enum

class Language(Enum):
    RUSSIAN = "ru"
    ENGLISH = "en"

class LocaleManager:
    """Менеджер локализации"""
    
    def __init__(self):
        self.current_language = Language.RUSSIAN
        self.translations = self._load_translations()
    
    def _load_translations(self) -> Dict[str, Dict[str, str]]:
        """Загружает все переводы"""
        return {
            "ru": {
                # Общие фразы
                "language_selection": "Пожалуйста, выберите язык:",
                "welcome": "Привет! Я твоя виртуальная подруга\nЯ так рада тебя видеть! Выбери режим, чтобы мы могли познакомиться поближе) Возможно даже слишком близко...",
                "age_verification": "🔞 Вам должно быть 18 лет или больше, чтобы продолжить использование этого бота.",
                "age_confirm": "🔞 Мне больше 18 лет",
                "start_game": "🔥 Начать игру",
                "ask_name": "Отлично! Как тебя зовут?",
                "choose_girl": "💖 Привет, {name}! Теперь выбери девушку, с которой хочешь начать общение:",
                "girl_description": "💡 Описание каждой девушки можно найти, нажав на кнопку c именем ^^",
                
                # Кнопки меню
                "start_chat": "💌 Начать общение",
                "games": "🎮 Игры",
                "hearts": "❤️ Мои очки",
                "profile": "👤 Профиль",
                "relationships": "💕 Отношения",
                "hot_pics": "🔥 Hot Pics (18+)",
                "personalize": "🎭 Персонализация",
                "back": "⬅️ Назад",
                "back_to_menu": "⬅️ В главное меню",
                
                # Девушки
                "girl_sakura": "Сакура",
                "girl_reiko": "Рэйко", 
                "girl_ayane": "Аяне",
                "girl_hikari": "Хикари",
                "girl_yuki": "Юки",
                "select_girl": "✅ Выбрать",
                "back_to_girls": "⬅️ Назад",
                
                # Отношения
                "relationship_status": "💖 Статус отношений с виртуальной подругой",
                "next_level": "Следующий уровень:",
                "sympathy_level": "💖 Уровень симпатии:",
                "closeness_points": "🌟 Очки близости:",
                "achievements": "🏆 Достижения:",
                "streak_days": "🔥 Дней подряд:",
                "active_days": "📅 Дней активности:",
                "total_messages": "💬 Всего сообщений:",
                "points_to_next": "💫 До следующего уровня:",
                "points": "очков",
                "mood_title": "Настроение девушки:",
                "current_mood": "💭 Текущее настроение:",
                "communication_style": "🎭 Стиль общения:",
                "relationship_level": "💖 Уровень отношений:",
                
                # Уровни отношений
                "level_1": "Знакомый",
                "level_2": "Друг", 
                "level_3": "Близкий человек",
                "level_4": "Особенный",
                "level_5": "Любимый человек",
                
                # Настроения
                "mood_happy": "Радостная и энергичная",
                "mood_sad": "Грустная и задумчивая",
                "mood_playful": "Игривая и веселая",
                "mood_caring": "Заботливая и понимающая",
                "mood_romantic": "Романтичная и страстная",
                "mood_shy": "Застенчивая и нежная",
                "mood_sarcastic": "Саркастичная и остроумная",
                "mood_thoughtful": "Задумчивая и философская",
                "mood_excited": "Воодушевленная и энергичная",
                "mood_melancholic": "Меланхоличная и ностальгичная",
                "mood_mischievous": "Озорная и игривая",
                "mood_nostalgic": "Ностальгичная и сентиментальная",
                
                # Стили общения
                "style_positive": "позитивная, воодушевляющая",
                "style_melancholic": "меланхоличная, сочувствующая",
                "style_ironic": "ироничная, с подколками",
                "style_analytical": "глубокая, аналитическая",
                "style_enthusiastic": "энтузиастичная, восторженная",
                "style_romantic": "грустно-романтичная, ностальгичная",
                "style_playful": "шаловливая, с подколками",
                "style_touching": "трогательная, с воспоминаниями",
                
                # Ошибки
                "validation_error": "❌ Ваше сообщение содержит недопустимый контент.",
                "rate_limit_error": "⏰ Слишком много запросов. Подождите немного.",
                "user_validation_error": "❌ Ошибка валидации пользователя.",
                "too_many_messages": "⏰ Слишком много сообщений. Подождите немного.",
                "banned_user": "Извини, ты заблокирован.",
                
                # Команды
                "mood_command": "Настроение",
                "profile_command": "Профиль", 
                "shop_command": "Магазин",
                "relationships_command": "Отношения",
                "buy_command": "Купить",
                "personalize_command": "Персонализация",
            },
            
            "en": {
                # General phrases
                "language_selection": "Please select a language:",
                "welcome": "Hello! I'm your virtual girlfriend\nI'm so happy to see you! Choose a mode so we can get to know each other better) Maybe even too close...",
                "age_verification": "🔞 You must be 18 years or older to continue using this bot.",
                "age_confirm": "🔞 I'm over 18 years old",
                "start_game": "🔥 Start Game",
                "ask_name": "Great! What's your name?",
                "choose_girl": "💖 Hello, {name}! Now choose the girl you want to start communicating with:",
                "girl_description": "💡 You can find a description of each girl by clicking on the button with the name ^^",
                
                # Menu buttons
                "start_chat": "💌 Start Chat",
                "games": "🎮 Games",
                "hearts": "❤️ My Points",
                "profile": "👤 Profile",
                "relationships": "💕 Relationships",
                "hot_pics": "🔥 Hot Pics (18+)",
                "personalize": "🎭 Personalization",
                "back": "⬅️ Back",
                "back_to_menu": "⬅️ To Main Menu",
                
                # Girls
                "girl_sakura": "Sakura",
                "girl_reiko": "Reiko",
                "girl_ayane": "Ayane", 
                "girl_hikari": "Hikari",
                "girl_yuki": "Yuki",
                "select_girl": "✅ Select",
                "back_to_girls": "⬅️ Back",
                
                # Relationships
                "relationship_status": "💖 Relationship status with virtual girlfriend",
                "next_level": "Next level:",
                "sympathy_level": "💖 Sympathy level:",
                "closeness_points": "🌟 Closeness points:",
                "achievements": "🏆 Achievements:",
                "streak_days": "🔥 Days in a row:",
                "active_days": "📅 Active days:",
                "total_messages": "💬 Total messages:",
                "points_to_next": "💫 To next level:",
                "points": "points",
                "mood_title": "Girl's mood:",
                "current_mood": "💭 Current mood:",
                "communication_style": "🎭 Communication style:",
                "relationship_level": "💖 Relationship level:",
                
                # Relationship levels
                "level_1": "Acquaintance",
                "level_2": "Friend",
                "level_3": "Close person", 
                "level_4": "Special",
                "level_5": "Beloved person",
                
                # Moods
                "mood_happy": "Happy and energetic",
                "mood_sad": "Sad and thoughtful",
                "mood_playful": "Playful and cheerful",
                "mood_caring": "Caring and understanding",
                "mood_romantic": "Romantic and passionate",
                "mood_shy": "Shy and gentle",
                "mood_sarcastic": "Sarcastic and witty",
                "mood_thoughtful": "Thoughtful and philosophical",
                "mood_excited": "Enthusiastic and energetic",
                "mood_melancholic": "Melancholic and nostalgic",
                "mood_mischievous": "Mischievous and playful",
                "mood_nostalgic": "Nostalgic and sentimental",
                
                # Communication styles
                "style_positive": "positive, inspiring",
                "style_melancholic": "melancholic, sympathetic",
                "style_ironic": "ironic, with teasing",
                "style_analytical": "deep, analytical",
                "style_enthusiastic": "enthusiastic, ecstatic",
                "style_romantic": "sad-romantic, nostalgic",
                "style_playful": "mischievous, with teasing",
                "style_touching": "touching, with memories",
                
                # Errors
                "validation_error": "❌ Your message contains unacceptable content.",
                "rate_limit_error": "⏰ Too many requests. Please wait a bit.",
                "user_validation_error": "❌ User validation error.",
                "too_many_messages": "⏰ Too many messages. Please wait a bit.",
                "banned_user": "Sorry, you're blocked.",
                
                # Commands
                "mood_command": "Mood",
                "profile_command": "Profile",
                "shop_command": "Shop", 
                "relationships_command": "Relationships",
                "buy_command": "Buy",
                "personalize_command": "Personalization",
                
                # Shop
                "shop_welcome": "🛒 Shop\n\nChoose a plan to purchase:",
                "payment_created": "💳 Payment Created",
                "payment_amount": "Amount:",
                "payment_description": "Description:",
                "payment_link": "Payment link:",
                "payment_valid": "Payment valid for 24 hours",
                "check_status": "✅ Check Status",
                "cancel_payment": "❌ Cancel",
                "back_to_shop": "⬅️ Back",
                "payment_success": "✅ Payment Successfully Processed!",
                "received_benefits": "🎁 Received Benefits:",
                "thanks_purchase": "💖 Thank you for your purchase!",
                "payment_not_completed": "Payment not completed",
                "payment_not_found": "Payment not found in active payments",
                "plan_not_found": "Plan not found",
                "payment_cancelled": "❌ Payment Cancelled",
                "back_to_shop": "⬅️ Back to Shop",
                "payment_error": "❌ Payment Error:",
                "unknown_error": "Unknown error",
                "payment_check_error": "❌ Payment Check Error",
                "payment_cancellation_error": "❌ Payment Cancellation Error",
            }
        }
    
    def set_language(self, language: Language):
        """Устанавливает язык"""
        self.current_language = language
    
    def get_language(self) -> Language:
        """Получает текущий язык"""
        return self.current_language
    
    def get_text(self, key: str, **kwargs) -> str:
        """Получает переведенный текст"""
        if self.current_language.value not in self.translations:
            self.current_language = Language.RUSSIAN
        
        text = self.translations[self.current_language.value].get(key, key)
        
        # Заменяем параметры в тексте
        if kwargs:
            try:
                text = text.format(**kwargs)
            except KeyError:
                pass
        
        return text
    
    def get_relationship_level_name(self, level: int) -> str:
        """Получает название уровня отношений"""
        level_key = f"level_{level}"
        return self.get_text(level_key)
    
    def get_mood_description(self, mood: str) -> str:
        """Получает описание настроения"""
        mood_key = f"mood_{mood}"
        return self.get_text(mood_key)
    
    def get_communication_style(self, style: str) -> str:
        """Получает описание стиля общения"""
        style_key = f"style_{style}"
        return self.get_text(style_key)

# Глобальный экземпляр менеджера локализации
locale_manager = LocaleManager()
