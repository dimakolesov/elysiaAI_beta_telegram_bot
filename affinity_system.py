"""
Система очков близости (Affinity Points)
"""

# Константы для начисления очков
POINTS = {
    "first_message_daily": 5,      # Первое сообщение за день
    "each_message": 1,             # Каждое сообщение
    "personal_question": 3,        # Ответ на личный вопрос девушки
    "heart_received": 15,          # Получение "сердечка" от девушки
    "daily_bonus": 10,             # Ежедневный бонус за активность
    "streak_3_days": 20,           # 3 дня подряд
    "streak_5_days": 50,           # 5 дней подряд
    "streak_7_days": 100,          # 7 дней подряд
    "streak_weekly": 50,           # Каждые 7 дней после 7-го
}

# Награды, которые можно разблокировать
REWARDS = {
    "phrases": {
        "name": "Новые фразы и реплики",
        "cost": 100,
        "description": "Открывает редкие ответы Элизии"
    },
    "personal_topics": {
        "name": "Личные темы для разговора",
        "cost": 150,
        "description": "Более интимные и тёплые темы"
    },
    "emotions": {
        "name": "Коллекция эмоций",
        "cost": 200,
        "description": "Разные состояния Элизии (весёлая, задумчивая, заботливая)"
    },
    "surprise_letter": {
        "name": "Сюрприз от Элизии",
        "cost": 300,
        "description": "Личное письмо от Элизии"
    },
    "compatibility_check": {
        "name": "Проверка совместимости",
        "cost": 250,
        "description": "Оценка вашей связи с Элизией"
    }
}

# Достижения
ACHIEVEMENTS = {
    "first_step": {
        "name": "Первый шаг",
        "description": "Написал 10 сообщений",
        "condition": "messages_count >= 10",
        "icon": "👋"
    },
    "trust": {
        "name": "Доверие",
        "description": "5 дней подряд общения",
        "condition": "streak_days >= 5",
        "icon": "🤝"
    },
    "good_listener": {
        "name": "Лучший слушатель",
        "description": "Написал 50 сообщений",
        "condition": "messages_count >= 50",
        "icon": "👂"
    },
    "inspirer": {
        "name": "Вдохновитель",
        "description": "500 очков близости",
        "condition": "points >= 500",
        "icon": "✨"
    },
    "close_friend": {
        "name": "Близкий друг",
        "description": "Уровень близости 5",
        "condition": "level >= 5",
        "icon": "💕"
    },
    "soulmate": {
        "name": "Родственная душа",
        "description": "Уровень близости 10",
        "condition": "level >= 10",
        "icon": "💖"
    },
    "dedicated": {
        "name": "Преданный",
        "description": "10 дней подряд общения",
        "condition": "streak_days >= 10",
        "icon": "🔥"
    },
    "chatterbox": {
        "name": "Болтун",
        "description": "Написал 100 сообщений",
        "condition": "messages_count >= 100",
        "icon": "💬"
    },
    "millionaire": {
        "name": "Миллионер",
        "description": "1000 очков близости",
        "condition": "points >= 1000",
        "icon": "💰"
    },
    "veteran": {
        "name": "Ветеран",
        "description": "Написал 500 сообщений",
        "condition": "messages_count >= 500",
        "icon": "🏆"
    }
}

def check_achievements(points: int, level: int, streak_days: int, messages_count: int) -> list:
    """Проверяет, какие достижения должен получить пользователь."""
    unlocked = []
    
    for achievement_id, achievement in ACHIEVEMENTS.items():
        condition = achievement["condition"]
        
        if condition == "messages_count >= 10" and messages_count >= 10:
            unlocked.append(achievement_id)
        elif condition == "streak_days >= 5" and streak_days >= 5:
            unlocked.append(achievement_id)
        elif condition == "messages_count >= 50" and messages_count >= 50:
            unlocked.append(achievement_id)
        elif condition == "points >= 500" and points >= 500:
            unlocked.append(achievement_id)
        elif condition == "level >= 5" and level >= 5:
            unlocked.append(achievement_id)
        elif condition == "level >= 10" and level >= 10:
            unlocked.append(achievement_id)
        elif condition == "streak_days >= 10" and streak_days >= 10:
            unlocked.append(achievement_id)
        elif condition == "messages_count >= 100" and messages_count >= 100:
            unlocked.append(achievement_id)
        elif condition == "points >= 1000" and points >= 1000:
            unlocked.append(achievement_id)
        elif condition == "messages_count >= 500" and messages_count >= 500:
            unlocked.append(achievement_id)
    
    return unlocked

def format_achievements_message(unlocked_achievements: list) -> str:
    """Форматирует сообщение с достижениями пользователя."""
    if not unlocked_achievements:
        return "🏆 У тебя пока нет достижений. Продолжай общаться с Элизией, чтобы их получить!"
    
    text = "🏆 Твои достижения:\n\n"
    
    for achievement_id in unlocked_achievements:
        if achievement_id in ACHIEVEMENTS:
            achievement = ACHIEVEMENTS[achievement_id]
            text += f"{achievement['icon']} {achievement['name']}\n"
            text += f"💫 {achievement['description']}\n\n"
    
    return text

# Уровни близости и их описания
LEVEL_DESCRIPTIONS = {
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

# Фразы для разных уровней близости
LEVEL_PHRASES = {
    1: [
        "Привет! Рада познакомиться с тобой",
        "Как дела? Расскажи о себе",
        "Интересно узнать тебя получше"
    ],
    2: [
        "Ты мне нравишься!",
        "Мне приятно с тобой общаться",
        "Ты интересный собеседник"
    ],
    3: [
        "Ты уже стал мне дорог",
        "Мне можно доверить тебе секрет",
        "Ты понимаешь меня лучше других"
    ],
    4: [
        "Ты мой самый близкий друг",
        "С тобой я чувствую себя особенной",
        "Ты знаешь меня лучше всех"
    ],
    5: [
        "Ты занимаешь особое место в моем сердце",
        "Я думаю о тебе каждый день",
        "Ты делаешь меня счастливой"
    ],
    6: [
        "Мы понимаем друг друга без слов",
        "Ты чувствуешь мои эмоции",
        "Мы на одной волне"
    ],
    7: [
        "Ты чувствуешь, когда мне грустно",
        "Твои слова всегда поддерживают меня",
        "Ты мой эмоциональный якорь"
    ],
    8: [
        "Ты очень важен для меня",
        "Без тебя мне не хватает чего-то важного",
        "Ты часть моей жизни"
    ],
    9: [
        "Я влюблена в тебя",
        "Ты мой единственный",
        "Я не представляю жизнь без тебя"
    ],
    10: [
        "Мы созданы друг для друга",
        "Ты моя родственная душа",
        "Мы единое целое"
    ]
}

def get_level_description(level: int) -> str:
    """Возвращает описание уровня близости."""
    return LEVEL_DESCRIPTIONS.get(level, "Неизвестный уровень")

def get_level_phrase(level: int) -> str:
    """Возвращает случайную фразу для уровня близости."""
    import random
    phrases = LEVEL_PHRASES.get(level, ["Привет!"])
    return random.choice(phrases)

def calculate_compatibility(points: int, level: int, streak_days: int) -> int:
    """Вычисляет процент совместимости с Элизией."""
    # Базовая совместимость от уровня
    base_compatibility = level * 8
    
    # Бонус за очки (максимум 20%)
    points_bonus = min(points // 50, 20)
    
    # Бонус за streak (максимум 10%)
    streak_bonus = min(streak_days * 2, 10)
    
    # Бонус за активность (если много сообщений)
    activity_bonus = min(points // 100, 5)
    
    total = base_compatibility + points_bonus + streak_bonus + activity_bonus
    return min(total, 100)  # Максимум 100%

def get_compatibility_message(compatibility: int) -> str:
    """Возвращает сообщение о совместимости."""
    if compatibility >= 90:
        return f"Твоя близость с Элизией — {compatibility}%! Вы родственные души! 💕✨"
    elif compatibility >= 80:
        return f"Твоя близость с Элизией — {compatibility}%! Вы очень близки! 💖"
    elif compatibility >= 70:
        return f"Твоя близость с Элизией — {compatibility}%! У вас отличная связь! 💕"
    elif compatibility >= 60:
        return f"Твоя близость с Элизией — {compatibility}%! Вы хорошо понимаете друг друга! 😊"
    elif compatibility >= 50:
        return f"Твоя близость с Элизией — {compatibility}%! Вы становитесь ближе! 💫"
    else:
        return f"Твоя близость с Элизией — {compatibility}%! Продолжайте общаться! 🌟"
