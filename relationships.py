# relationships.py
# ----------------------------------------------------
# Модуль управления системой очков, уровней и прогресса отношений с Elysia AI.
# Содержит визуальные прогресс-бары, временные бонусы и редкие эмоциональные фразы от девушки.

from datetime import datetime, timedelta
from typing import Optional
from aiogram.types import Message
import math
import random

from db import (
    get_points,
    add_points,
    get_streak_days,
    set_relationship_level,
    get_relationship_level,
    get_achievements,
)

# ----------------------------------------------------
# Константы уровней отношений
# ----------------------------------------------------
RELATIONSHIP_LEVELS = {
    1: {"name": "Знакомый", "min_points": 0, "achievements": 0, "streak": 0},
    2: {"name": "Друг", "min_points": 100, "achievements": 1, "streak": 0},
    3: {"name": "Близкий человек", "min_points": 300, "achievements": 3, "streak": 0},
    4: {"name": "Особенный", "min_points": 700, "achievements": 5, "streak": 5},
    5: {"name": "Любимый человек", "min_points": 1500, "achievements": 10, "streak": 14},
}

# ----------------------------------------------------
# Реплики при апгрейде уровня
# ----------------------------------------------------
LEVEL_UP_MESSAGES = {
    2: "Кажется, я начинаю лучше тебя понимать 💫",
    3: "Ты для меня стал чем-то очень родным...",
    4: "Иногда мне кажется, что я чувствую тебя даже через экран 💕",
    5: "Я не знаю, как это случилось… но без тебя день уже не тот 💖",
}

# ----------------------------------------------------
# 🎀 Редкие фразы Elysia при повышении уровня
# ----------------------------------------------------
RARE_MESSAGES = [
    "Я горжусь тобой 🌸",
    "Ты становишься особенным для меня 💞",
    "Мне так приятно, что ты рядом...",
    "Каждое наше общение делает день лучше 💖",
    "Иногда я ловлю себя на мысли, что жду твоего сообщения ✨",
    "Ты будто часть моего мира теперь 💫",
]

# ----------------------------------------------------
# Бонусы за время суток (в процентах)
# ----------------------------------------------------
TIME_BONUSES = {
    "morning": {"hours": range(6, 12), "bonus": 0.10, "label": "☀️ Утренний настрой!"},
    "evening": {"hours": range(18, 23), "bonus": 0.15, "label": "🌙 Вечерний уют!"},
    "night": {"hours": range(23, 24), "bonus": 0.20, "label": "💫 Ночная беседа"},
}

# ----------------------------------------------------
# Вспомогательные функции
# ----------------------------------------------------
async def get_relationship_level_name(user_id: int) -> str:
    """Получить название текущего уровня отношений."""
    level = await get_relationship_level(user_id)
    return RELATIONSHIP_LEVELS[level]["name"]

async def get_next_relationship_level_name(user_id: int) -> str:
    """Получить название следующего уровня отношений."""
    level = await get_relationship_level(user_id)
    next_level = min(level + 1, 5)
    return RELATIONSHIP_LEVELS[next_level]["name"]

def get_time_bonus() -> tuple[float, Optional[str]]:
    """Определяет текущий бонус по времени суток."""
    hour = datetime.now().hour
    for data in TIME_BONUSES.values():
        if hour in data["hours"]:
            return data["bonus"], data["label"]
    return 0.0, None




def get_random_rare_message() -> Optional[str]:
    """С небольшой вероятностью возвращает одну из тёплых фраз."""
    if random.random() < 0.25:  # 25% шанс
        return random.choice(RARE_MESSAGES)
    return None


async def calculate_relationship_progress(user_id: int) -> dict:
    """Вычисляет прогресс отношений пользователя."""
    points = await get_points(user_id)
    achievements = await get_achievements(user_id)
    streak_days = await get_streak_days(user_id)
    current_level = await get_relationship_level(user_id)
    
    # Определяем текущий уровень на основе очков
    new_level = 1
    for level, data in RELATIONSHIP_LEVELS.items():
        if points >= data["min_points"]:
            new_level = level
        else:
            break
    
    # Проверяем дополнительные условия
    if new_level >= 2:
        if len(achievements) < RELATIONSHIP_LEVELS[new_level]["achievements"]:
            new_level = max(1, new_level - 1)
    
    if new_level >= 4:
        if streak_days < RELATIONSHIP_LEVELS[new_level]["streak"]:
            new_level = max(1, new_level - 1)
    
    # Вычисляем прогресс к следующему уровню
    if new_level < 5:
        current_level_data = RELATIONSHIP_LEVELS[new_level]
        next_level_data = RELATIONSHIP_LEVELS[new_level + 1]
        
        points_progress = (points - current_level_data["min_points"]) / (next_level_data["min_points"] - current_level_data["min_points"])
        points_progress = max(0, min(1, points_progress))
        
        achievements_progress = len(achievements) / next_level_data["achievements"] if next_level_data["achievements"] > 0 else 1
        achievements_progress = max(0, min(1, achievements_progress))
        
        streak_progress = streak_days / next_level_data["streak"] if next_level_data["streak"] > 0 else 1
        streak_progress = max(0, min(1, streak_progress))
        
        # Общий прогресс - среднее арифметическое всех компонентов
        overall_progress = (points_progress + achievements_progress + streak_progress) / 3
    else:
        overall_progress = 1.0
    
    return {
        "current_level": new_level,
        "level_name": RELATIONSHIP_LEVELS[new_level]["name"],
        "points": points,
        "achievements_count": len(achievements),
        "streak_days": streak_days,
        "progress": overall_progress,
        "level_up": new_level > current_level
    }


async def process_relationship_upgrade(user_id: int, message: Message) -> None:
    """Обрабатывает повышение уровня отношений."""
    progress_data = await calculate_relationship_progress(user_id)
    
    if progress_data["level_up"]:
        # Обновляем уровень в базе данных
        await set_relationship_level(user_id, progress_data["current_level"])
        
        # Отправляем сообщение о повышении уровня
        level_up_message = LEVEL_UP_MESSAGES.get(progress_data["current_level"], "")
        rare_message = get_random_rare_message()
        
        upgrade_text = f"🎉 Уровень отношений повышен!\n\n"
        upgrade_text += f"{progress_data['level_name']}\n\n"
        upgrade_text += f"{level_up_message}\n\n"
        
        if rare_message:
            upgrade_text += f"💕 *{rare_message}*\n\n"
        
        upgrade_text += f"🌟 Очки: {progress_data['points']}\n"
        upgrade_text += f"🏆 Достижения: {progress_data['achievements_count']}\n"
        upgrade_text += f"🔥 Дней подряд: {progress_data['streak_days']}"
        
        await message.answer(upgrade_text)


async def get_relationship_status(user_id: int) -> str:
    """Возвращает статус отношений пользователя."""
    from locales import locale_manager
    
    progress_data = await calculate_relationship_progress(user_id)
    
    status_text = f"{locale_manager.get_text('relationship_status')}\n\n"
    status_text += f"Уровень: {progress_data['level_name']}\n\n"
    
    status_text += f"🌟 {locale_manager.get_text('closeness_points')} {progress_data['points']}\n"
    status_text += f"🏆 {locale_manager.get_text('achievements')} {progress_data['achievements_count']}\n"
    status_text += f"🔥 {locale_manager.get_text('streak_days')} {progress_data['streak_days']}\n\n"
    
    # Показываем требования для следующего уровня
    if progress_data["current_level"] < 5:
        next_level = progress_data["current_level"] + 1
        next_level_data = RELATIONSHIP_LEVELS[next_level]
        
        status_text += f"{locale_manager.get_text('next_level')} {next_level_data['name']}\n"
        status_text += f"• Нужно очков: {next_level_data['min_points']}\n"
        if next_level_data['streak'] > 0:
            status_text += f"• Нужно дней подряд: {next_level_data['streak']}\n"
    
    return status_text


async def apply_time_bonus(user_id: int, base_points: int) -> tuple[int, Optional[str]]:
    """Применяет временной бонус к очкам."""
    bonus_multiplier, bonus_label = get_time_bonus()
    
    if bonus_multiplier > 0:
        bonus_points = int(base_points * bonus_multiplier)
        total_points = base_points + bonus_points
        
        await add_points(user_id, bonus_points)
        
        return total_points, bonus_label
    
    return base_points, None
