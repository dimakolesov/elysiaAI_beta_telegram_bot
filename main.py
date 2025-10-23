from __future__ import annotations

import asyncio
import os
import random
from datetime import datetime, timedelta
from functools import wraps

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.enums import ChatAction

# Импортируем новые системы безопасности
from config import config
from validation import validator
from rate_limiter import rate_limiter, cleanup_task
from logger import bot_logger, log_performance
from error_handler import handle_errors, handle_telegram_errors, retry_on_error
from locales import locale_manager, Language
from yoomoney import payment_manager, cleanup_payments_task
from payment_system import payment_processor
from trial_system import trial_system
from admin_system import admin_system
from telegram_stars import stars_payment
from referral_system import referral_system

from db import (
    add_hearts, get_achievements, get_gender, get_girl, get_hearts,
    get_memory, get_mood, get_relationship_level, get_total_messages, get_user_name,
    grant_access, init_db, is_banned, save_message, set_gender,
    set_girl, set_mood, set_relationship_level, set_user_name, upsert_user,
    add_achievement, get_all_user_ids,
    add_points, get_points, get_level, level_up, update_streak, 
    get_streak_days, unlock_reward, get_unlocked_rewards, get_level_progress,
    get_user_trial_status, set_user_trial_status, ban_user, unset_ban,
    process_referral, has_referrer, process_subscription_referral
)
from llm import ask_llm
from memory import serialize_memory, get_memory_summary
from game_handlers import game_router, get_flirt_level, get_flirt_description
from personalization_handlers import personalization_router
from affinity_system import POINTS, REWARDS, ACHIEVEMENTS, get_level_description, get_level_phrase, calculate_compatibility, get_compatibility_message, check_achievements as check_affinity_achievements
from sympathy_system import SympathySystem, InteractionType
from personality_system import PersonalitySystem, MoodType
from advanced_memory import AdvancedMemorySystem
from relationships import process_relationship_upgrade, get_relationship_status, apply_time_bonus, get_relationship_level_name, get_next_relationship_level_name
from hot_pic_system import (
    hot_pic_manager, handle_hot_pic_message, start_hot_pic_mode, 
    send_first_hot_pic, send_hot_pic_with_caption, cleanup_expired_sessions_task
)
from utils import (
    TEXTS, MOODS, ACHIEVEMENTS, ROLEPLAY_GAMES,
    kb_tariff, kb_gender, kb_main_menu, kb_moods, kb_games,
    kb_roleplay_games, kb_roleplay_game_description, kb_roleplay_actions,
    format_hearts_message,
    get_next_achievement, get_girl_photo_path
)

# Фразы для индикатора "Печатает..."
THINKING_PHRASES = [
    "Печатает... 💭",
    "Печатает... 🤔",
    "Печатает... ✨",
    "Печатает... 💕",
    "Печатает... 😊",
    "Печатает... 💖",
    "Печатает... 😘",
    "Печатает... 🌟"
]

def send_typing_action(func):
    """Декоратор для показа индикатора печати при обработке сообщений."""
    @wraps(func)
    async def wrapper(message: Message, state: FSMContext, *args, **kwargs):
        # Показываем индикатор печати
        await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
        # Небольшая задержка для эффекта
        await asyncio.sleep(0.5)
        # Выполняем оригинальную функцию
        return await func(message, state, *args, **kwargs)
    return wrapper


def get_girls_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру с девушками, их возрастом и сердечками."""
    girl_info = {
        "girl_sakura": {"name": locale_manager.get_text("girl_sakura"), "age": "20 лет" if locale_manager.get_language() == Language.RUSSIAN else "20 years"},
        "girl_reiko": {"name": locale_manager.get_text("girl_reiko"), "age": "24 года" if locale_manager.get_language() == Language.RUSSIAN else "24 years"},
        "girl_ayane": {"name": locale_manager.get_text("girl_ayane"), "age": "28 лет" if locale_manager.get_language() == Language.RUSSIAN else "28 years"},
        "girl_hikari": {"name": locale_manager.get_text("girl_hikari"), "age": "26 лет" if locale_manager.get_language() == Language.RUSSIAN else "26 years"},
        "girl_yuki": {"name": locale_manager.get_text("girl_yuki"), "age": "22 года" if locale_manager.get_language() == Language.RUSSIAN else "22 years"}
    }
    
    buttons = []
    for girl_id, info in girl_info.items():
        buttons.append([InlineKeyboardButton(
            text=f"♥ {info['name']} ({info['age']})", 
            callback_data=girl_id
        )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

async def show_thinking_indicator(chat_id: int) -> Message:
    """Показывает индикатор 'Печатает...' с анимацией."""
    thinking_msg = random.choice(THINKING_PHRASES)
    # Отправляем сообщение с индикатором печати
    return await bot.send_message(chat_id, thinking_msg)


# FSM состояния
class Onboarding(StatesGroup):
    language_selection = State()
    age_verification = State()
    choosing_tariff = State()
    asking_name = State()
    choosing_girl = State()

class RoleplayStates(StatesGroup):
    choosing_game = State()
    playing_game = State()


class Chatting(StatesGroup):
    active_chat = State()

class HotPicsStates(StatesGroup):
    waiting_for_prompt = State()
    generating_image = State()
    hot_pic_mode = State()


# Router
from aiogram import Router
router = Router()

# Глобальная переменная для бота (будет инициализирована в main)
bot = None

# Инициализация систем
sympathy_system = SympathySystem()
personality_system = PersonalitySystem()
memory_system = AdvancedMemorySystem()

async def check_premium_access(user_id: int, username: str = None) -> bool:
    """Проверяет, есть ли у пользователя доступ к премиум функциям"""
    try:
        # Проверяем, является ли пользователь админом
        if username and admin_system.is_admin(username):
            return True
        
        # Проверяем активную подписку
        access_info = await grant_access(user_id, 0)  # Проверяем без добавления дней
        if access_info and access_info.get('has_access', False):
            return True
        
        # Проверяем пробный день
        trial_status = await get_user_trial_status(user_id)
        if trial_status == "active":
            return True
        
        return False
        
    except Exception as e:
        bot_logger.log_system_error(e, f"Failed to check premium access for user {user_id}")
        return False

async def check_hot_pics_access(user_id: int) -> bool:
    """Проверяет доступ к Hot Pics (только для платных пользователей)"""
    try:
        # Hot Pics доступны только платным пользователям, не пробным
        access_info = await grant_access(user_id, 0)
        if access_info and access_info.get('has_access', False):
            # Проверяем, что это не пробный день
            trial_status = await get_user_trial_status(user_id)
            if trial_status != "active":
                return True
        
        return False
        
    except Exception as e:
        bot_logger.log_system_error(e, f"Failed to check hot pics access for user {user_id}")
        return False




@router.message(Command("admin"))
@handle_errors
@handle_telegram_errors
async def admin_handler(message: Message, state: FSMContext) -> None:
    """Обработчик админ команды /admin"""
    
    # Проверяем, является ли пользователь админом
    if not admin_system.is_admin(message.from_user.username):
        await message.answer("❌ У вас нет прав администратора")
        return
    
    # Проверка rate limiting
    if not await rate_limiter.is_allowed(message.from_user.id, 'message'):
        await message.answer("⏰ Слишком много запросов. Подождите немного.")
        return
    
    # Логирование
    bot_logger.log_admin_action("admin_command", {
        "user_id": message.from_user.id,
        "username": message.from_user.username,
        "text": message.text
    })
    
    try:
        # Парсим команду
        command_text = message.text.strip()
        parts = command_text.split()
        
        if len(parts) < 2:
            # Показываем справку
            help_text = admin_system.get_admin_help()
            await message.answer(help_text)
            return
        
        # Извлекаем команду и аргументы
        command = parts[1]
        args = parts[2:] if len(parts) > 2 else []
        
        # Обрабатываем команду
        result = await admin_system.process_admin_command(command, args)
        await message.answer(result)
        
    except Exception as e:
        bot_logger.log_system_error(e, f"Admin command failed for user {message.from_user.id}")
        await message.answer("❌ Ошибка выполнения админ команды")

@router.message(CommandStart())
@handle_errors
@handle_telegram_errors
async def start_handler(message: Message, state: FSMContext) -> None:
    """Обработчик команды /start."""
    
    # Валидация пользователя
    user_validation = validator.validate_user_id(message.from_user.id)
    if not user_validation.is_valid:
        bot_logger.log_security_event("invalid_user_id", message.from_user.id, user_validation.error_message)
        await message.answer("❌ Ошибка валидации пользователя.")
        return
    
    # Проверка rate limiting
    if not await rate_limiter.is_allowed(message.from_user.id, 'command'):
        bot_logger.log_rate_limit(message.from_user.id, 'command', blocked=True)
        await message.answer("⏰ Слишком много запросов. Подождите немного.")
        return
    
    # Логирование команды
    bot_logger.log_command(message.from_user.id, "/start")
    
    await init_db()
    await upsert_user(message.from_user.id, message.from_user.username)
    
    # Проверяем, не забанен ли пользователь
    if await is_banned(message.from_user.id):
        bot_logger.log_security_event("banned_user_attempt", message.from_user.id, "Attempted to start bot")
        await message.answer("Извини, ты заблокирован.")
        return
    
    # Обработка реферальной ссылки
    referrer_id = None
    if " " in message.text:
        try:
            referrer_candidate = int(message.text.split()[1])
            # Проверяем, что пользователь не приглашает сам себя
            if message.from_user.id != referrer_candidate:
                # Проверяем, что у пользователя еще нет реферера
                if not await has_referrer(message.from_user.id):
                    # Обрабатываем реферал
                    success = await referral_system.process_referral_registration(
                        message.from_user.id, referrer_candidate
                    )
                    if success:
                        referrer_id = referrer_candidate
                        bot_logger.log_info(f"Referral processed: {referrer_candidate} -> {message.from_user.id}")
        except (ValueError, IndexError):
            pass  # Игнорируем некорректные данные в ссылке
    
    # Начинаем с выбора языка
    await state.set_state(Onboarding.language_selection)
    
    # Если есть реферер, показываем специальное сообщение
    if referrer_id:
        await message.answer(
            f"🎉 Добро пожаловать!\n\n"
            f"Ты пришел по реферальной ссылке! Это значит, что кто-то из твоих друзей уже пользуется нашим ботом.\n\n"
            f"Please select a language:",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
                    [InlineKeyboardButton(text="🇺🇸 English", callback_data="lang_en")]
                ]
            )
        )
    else:
        await message.answer(
            "Please select a language:",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
                    [InlineKeyboardButton(text="🇺🇸 English", callback_data="lang_en")]
                ]
            )
        )


@router.callback_query(F.data == "lang_ru")
async def language_ru_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик выбора русского языка."""
    locale_manager.set_language(Language.RUSSIAN)
    await state.set_state(Onboarding.age_verification)
    await callback.message.edit_text(
        locale_manager.get_text("age_verification"),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=locale_manager.get_text("age_confirm"), callback_data="age_confirm")]
            ]
        )
    )
    await callback.answer()

@router.callback_query(F.data == "lang_en")
async def language_en_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик выбора английского языка."""
    locale_manager.set_language(Language.ENGLISH)
    await state.set_state(Onboarding.age_verification)
    await callback.message.edit_text(
        locale_manager.get_text("age_verification"),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=locale_manager.get_text("age_confirm"), callback_data="age_confirm")]
            ]
        )
    )
    await callback.answer()

@router.callback_query(F.data == "age_confirm")
async def age_confirm_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик подтверждения возраста."""
    await callback.answer()
    
    # Показываем приветственное сообщение с кнопкой "Начать игру"
    await state.set_state(Onboarding.choosing_tariff)
    await callback.message.answer(
        locale_manager.get_text("welcome"),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=locale_manager.get_text("start_game"), callback_data="start_game")]
            ]
        )
    )


@router.callback_query(F.data == "start_game")
async def start_game_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик кнопки 'Начать игру'."""
    await callback.answer()
    
    # Переходим к вводу имени
    await state.set_state(Onboarding.asking_name)
    await callback.message.answer(locale_manager.get_text("ask_name"))


@router.message(Command("mood"))
async def mood_handler(message: Message, state: FSMContext) -> None:
    """Обработчик команды /mood - показывает текущее настроение Элизии."""

    # Получаем текущее настроение
    current_mood = await personality_system.get_current_mood(message.from_user.id)
    mood_config = personality_system.mood_configs[current_mood]
    
    # Получаем информацию о пользователе
    user_name = await get_user_name(message.from_user.id)
    relationship_level = await get_relationship_level(message.from_user.id)
    
    mood_text = f"""
{mood_config['emoji']} {locale_manager.get_text('mood_title')}

👤 Пользователь: {user_name or f"ID: {message.from_user.id}"}

💭 {locale_manager.get_text('current_mood')} {mood_config['description']}
🎭 {locale_manager.get_text('communication_style')} {mood_config['response_style']}
💖 {locale_manager.get_text('relationship_level')} {relationship_level}/5

{mood_config['emoji']} {random.choice(mood_config['phrases'])}
"""

    await message.answer(mood_text, reply_markup=kb_main_menu())



@router.message(Command("profile"))
async def profile_handler(message: Message, state: FSMContext) -> None:
    """Обработчик команды /profile - показывает профиль с очками близости."""
    
    # Получаем данные пользователя
    user_name = await get_user_name(message.from_user.id)
    points = await get_points(message.from_user.id)
    level = await get_level(message.from_user.id)
    streak_days = await get_streak_days(message.from_user.id)
    hearts = await get_hearts(message.from_user.id)
    total_messages = await get_total_messages(message.from_user.id)
    
    # Вычисляем совместимость
    compatibility = calculate_compatibility(points, level, streak_days)
    
    # Получаем username или ID пользователя
    user_display = f"@{message.from_user.username}" if message.from_user.username else f"ID: {message.from_user.id}"
    
    # Получаем описание уровня
    level_description = get_level_description(level)
    
    profile_text = f"""
👤 Профиль {user_display}

💖 Уровень близости: {level}/10
📝 Описание: {level_description}

🌟 Очки близости: {points}
🔥 Дней подряд: {streak_days}
💕 Сердечки: {hearts}
💬 Сообщений: {total_messages}

💫 Совместимость с Элизией: {compatibility}%
{get_compatibility_message(compatibility)}
"""
    
    await message.answer(profile_text, reply_markup=kb_main_menu())


@router.message(Command("shop"))
async def shop_handler(message: Message, state: FSMContext) -> None:
    """Обработчик команды /shop - магазин наград за очки близости."""
    
    points = await get_points(message.from_user.id)
    unlocked_rewards = await get_unlocked_rewards(message.from_user.id)
    unlocked_names = {name for _, name in unlocked_rewards}
    
    shop_text = f"🛍️ Магазин наград\n\n💰 Твои очки: {points}\n\n"
    
    for reward_id, reward_data in REWARDS.items():
        status = "✅ Разблокировано" if reward_data["name"] in unlocked_names else f"🔒 {reward_data['cost']} очков"
        shop_text += f"{reward_data['name']}\n"
        shop_text += f"💎 {reward_data['description']}\n"
        shop_text += f"📊 {status}\n\n"
    
    shop_text += "💡 Используй /buy <название> для покупки награды!"
    
    await message.answer(shop_text, reply_markup=kb_main_menu())


@router.message(Command("relationships"))
async def relationships_handler(message: Message, state: FSMContext) -> None:
    """Обработчик команды /relationships - показывает статус отношений с Элизией."""

    status_text = await get_relationship_status(message.from_user.id)
    await message.answer(status_text, reply_markup=kb_main_menu())


@router.message(Command("buy"))
async def buy_handler(message: Message, state: FSMContext) -> None:
    """Обработчик покупки наград."""
    
    # Извлекаем название награды из команды
    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) < 2:
        await message.answer("Использование: /buy <название награды>")
        return
    
    reward_name = command_parts[1].strip()
    
    # Ищем награду по названию
    reward_id = None
    for rid, rdata in REWARDS.items():
        if rdata["name"].lower() == reward_name.lower():
            reward_id = rid
            break
    
    if not reward_id:
        await message.answer("❌ Награда не найдена! Используй /shop для просмотра доступных наград.")
        return
    
    reward_data = REWARDS[reward_id]
    points = await get_points(message.from_user.id)
    
    if points < reward_data["cost"]:
        await message.answer(f"❌ Недостаточно очков! Нужно {reward_data['cost']}, у тебя {points}")
        return
    
    # Проверяем, не разблокирована ли уже
    unlocked_rewards = await get_unlocked_rewards(message.from_user.id)
    unlocked_names = {name for _, name in unlocked_rewards}
    
    if reward_data["name"] in unlocked_names:
        await message.answer("✅ Эта награда уже разблокирована!")
        return
    
    # Покупаем награду
    await add_points(message.from_user.id, -reward_data["cost"])
    success = await unlock_reward(message.from_user.id, reward_id, reward_data["name"])
    
    if success:
        await message.answer(
            f"🎉 Поздравляю! Ты разблокировал награду:\n"
            f"{reward_data['name']}\n"
            f"💎 {reward_data['description']}\n\n"
            f"💰 Потрачено: {reward_data['cost']} очков\n"
            f"💫 Осталось: {points - reward_data['cost']} очков"
        )
    else:
        await message.answer("❌ Ошибка при покупке награды. Попробуй еще раз.")








@router.callback_query(F.data == "trial")
async def tariff_trial_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик выбора пробного тарифа."""
    await grant_access(callback.from_user.id, days=1, access_type="trial")
    await state.set_state(Onboarding.asking_name)
    await callback.answer()
    await callback.message.answer(TEXTS["ask_name"])


@router.callback_query(F.data == "paid")
async def tariff_paid_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик выбора платного тарифа."""
    await grant_access(callback.from_user.id, days=30, access_type="paid")
    await state.set_state(Onboarding.asking_name)
    await callback.answer()
    await callback.message.answer(TEXTS["ask_name"])


@router.message(Onboarding.asking_name)
async def enter_name_handler(message: Message, state: FSMContext) -> None:
    """Обработчик ввода имени."""
    user_name = (message.text or "").strip()
    if not user_name:
        await message.answer(locale_manager.get_text("ask_name"))
        return
    
    await set_user_name(message.from_user.id, user_name)
    await set_gender(message.from_user.id, "male")  # Устанавливаем по умолчанию
    
    # Переходим к выбору девушки
    await state.set_state(Onboarding.choosing_girl)
    await message.answer(
        locale_manager.get_text("choose_girl", name=user_name) + "\n\n" + locale_manager.get_text("girl_description"),
        reply_markup=get_girls_keyboard()
    )






@router.callback_query(F.data == "start_chat")
async def start_chat_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик начала чата."""
    
    await state.set_state(Chatting.active_chat)
    await callback.answer()
    await callback.message.answer("💬 Напиши мне что-нибудь, и я отвечу! Я так жду твоего сообщения, мой милый 😘")


@router.message()
@handle_errors
@handle_telegram_errors
@send_typing_action
async def chat_handler(message: Message, state: FSMContext) -> None:
    """Обработчик чата."""
    
    # Валидация сообщения
    message_validation = validator.validate_message(message.text or "", 'text')
    if not message_validation.is_valid:
        bot_logger.log_validation_error(message.from_user.id, "invalid_message", message.text or "")
        await message.answer("❌ Ваше сообщение содержит недопустимый контент.")
        return
    
    # Проверка rate limiting
    if not await rate_limiter.is_allowed(message.from_user.id, 'message'):
        bot_logger.log_rate_limit(message.from_user.id, 'message', blocked=True)
        await message.answer("⏰ Слишком много сообщений. Подождите немного.")
        return
    
    # Логирование сообщения
    bot_logger.log_message(message.from_user.id, message.text or "", "text")
    
    # Проверяем, находится ли пользователь в Hot Pic режиме
    current_state = await state.get_state()
    if current_state == HotPicsStates.hot_pic_mode:
        await handle_hot_pic_message(bot, message.from_user.id, message.text or "")
        return
    
    # Получаем контекст
    girl = await get_girl(message.from_user.id)
    mood = await get_mood(message.from_user.id)
    relationship_level = await get_relationship_level(message.from_user.id)
    gender = await get_gender(message.from_user.id)
    total_messages = await get_total_messages(message.from_user.id)
    
    # Определяем уровень флирта
    flirt_level = get_flirt_level(total_messages)
    flirt_description = get_flirt_description(flirt_level)
    
    # Сохраняем сообщение пользователя
    await save_message(message.from_user.id, message.text or "", role="user")
    
    # ==================== СИСТЕМА ОЧКОВ СИМПАТИИ ====================
    # Обрабатываем сообщение через новую систему симпатии
    sympathy_result = await sympathy_system.process_message(message.from_user.id, message.text or "")

    # Обновляем streak и получаем бонусные очки (старая система для совместимости)
    streak_bonus = await update_streak(message.from_user.id)

    # Применяем временные бонусы к очкам симпатии
    total_points, time_bonus_label = await apply_time_bonus(message.from_user.id, sympathy_result['points_change'])

    # Проверяем повышение уровня
    old_level = await get_level(message.from_user.id)
    await level_up(message.from_user.id)
    new_level = await get_level(message.from_user.id)

    # ==================== СИСТЕМА НАСТРОЕНИЯ И ПАМЯТИ ====================
    # Проверяем смену настроения
    mood_change = await personality_system.process_mood_change(message.from_user.id)
    
    # Обновляем память и контекст
    await memory_system.update_memory_context(message.from_user.id, message.text or "", "")
    
    # Получаем контекст памяти для ответа
    memory_context = await memory_system.get_memory_context(message.from_user.id)
    
    # Получаем память
    mem_pairs = await get_memory(message.from_user.id, limit=10)
    mem_text = serialize_memory(mem_pairs)
    
    # Показываем индикатор "Печатает..."
    thinking_msg = await show_thinking_indicator(message.chat.id)
    
    # Небольшая задержка чтобы пользователь увидел индикатор
    await asyncio.sleep(1)
    
    # Получаем настройки персонализации
    from db import get_personalization_settings
    personalization_settings = await get_personalization_settings(message.from_user.id)
    
    # Получаем ответ от ИИ
    reply = await ask_llm(
        message.text or "", 
        girl=girl, 
        mood=mood,
        relationship_level=relationship_level,
        memory=mem_text,
        gender=gender,
        flirt_level=flirt_level,
        flirt_description=flirt_description,
        memory_context=memory_context,
        current_mood=mood,
        personalization_settings=personalization_settings
    )
    
    # Удаляем индикатор "думает"
    await thinking_msg.delete()
    
    # Сохраняем ответ
    await save_message(message.from_user.id, reply, role="assistant")
    
    # Добавляем очки симпатии
    hearts_to_add = random.randint(1, 3)
    await add_hearts(message.from_user.id, hearts_to_add)
    
    # Проверяем достижения
    await check_achievements(message.from_user.id)
    
    # Отправляем ответ
    await message.answer(reply)
    
    # Проверяем повышение уровня отношений
    await process_relationship_upgrade(message.from_user.id, message)
    
    # ==================== УВЕДОМЛЕНИЯ О СИСТЕМЕ СИМПАТИИ ====================
    # Уведомления отключены по запросу пользователя


@router.callback_query(F.data == "hearts")
async def hearts_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик просмотра очков."""
    hearts = await get_hearts(callback.from_user.id)
    total_messages = await get_total_messages(callback.from_user.id)
    
    await callback.answer()
    await callback.message.answer(
        format_hearts_message(hearts, total_messages),
        reply_markup=kb_main_menu()
    )




@router.callback_query(F.data == "relationships")
async def relationships_callback_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик кнопки отношений и настроения."""

    # Получаем информацию об отношениях
    status_text = await get_relationship_status(callback.from_user.id)
    
    # Получаем статистику симпатии
    stats = await sympathy_system.get_user_stats(callback.from_user.id)
    user_name = await get_user_name(callback.from_user.id)
    
    # Получаем текущее настроение
    current_mood = await personality_system.get_current_mood(callback.from_user.id)
    mood_config = personality_system.mood_configs[current_mood]
    relationship_level = await get_relationship_level(callback.from_user.id)
    
    # Объединяем всю информацию
    combined_text = f"""
👤 Пользователь: {user_name or f"ID: {callback.from_user.id}"}
💖 Статус отношений с Элизией: {await get_relationship_level_name(callback.from_user.id)}
Следующий уровень: {await get_next_relationship_level_name(callback.from_user.id)}

💖 Уровень симпатии: {stats['level']}/10
🌟 Очки близости: {stats['points']}
🏆 Достижения: {stats['achievements_count']}
🔥 Дней подряд: {stats['streak_days']}
📅 Дней активности: {stats['days_active']}
💬 Всего сообщений: {stats['total_messages']}
💫 До следующего уровня: {stats['points_to_next_level']} очков

{mood_config['emoji']} {locale_manager.get_text('mood_title')} 

💭 {locale_manager.get_text('current_mood')} {mood_config['description']}
🎭 {locale_manager.get_text('communication_style')} {mood_config['response_style']}
💖 {locale_manager.get_text('relationship_level')} {relationship_level}/5
"""

    await callback.answer()
    await callback.message.answer(combined_text, reply_markup=kb_main_menu())




@router.callback_query(F.data == "profile")
async def profile_callback_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик кнопки профиля."""
    
    # Получаем данные пользователя
    user_name = await get_user_name(callback.from_user.id)
    points = await get_points(callback.from_user.id)
    level = await get_level(callback.from_user.id)
    streak_days = await get_streak_days(callback.from_user.id)
    hearts = await get_hearts(callback.from_user.id)
    total_messages = await get_total_messages(callback.from_user.id)
    
    # Вычисляем совместимость
    compatibility = calculate_compatibility(points, level, streak_days)
    
    # Получаем username или ID пользователя
    user_display = f"@{callback.from_user.username}" if callback.from_user.username else f"ID: {callback.from_user.id}"
    
    # Получаем описание уровня
    level_description = get_level_description(level)
    
    profile_text = f"""
👤 Профиль {user_display}

💖 Уровень близости: {level}/10
📝 Описание: {level_description}

🌟 Очки близости: {points}
🔥 Дней подряд: {streak_days}
💕 Сердечки: {hearts}
💬 Сообщений: {total_messages}

💫 Совместимость с Элизией: {compatibility}%
{get_compatibility_message(compatibility)}
"""
    
    await callback.answer()
    await callback.message.answer(profile_text, reply_markup=kb_main_menu())


@router.callback_query(F.data == "games")
async def games_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик игр."""
    await callback.answer()
    await callback.message.answer("🎮 Выбери игру, в которую хочешь поиграть со мной, мой милый 😘:", reply_markup=kb_games())





@router.callback_query(F.data == "back_to_menu")
async def back_to_menu_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Возврат в главное меню."""
    await state.clear()
    await callback.message.answer(
        "👋 Привет! Я твоя виртуальная подруга! 😊\n\n"
        "Я здесь, чтобы составить тебе компанию, поддержать и просто поговорить. "
        "Расскажи мне о себе, поделись мыслями или просто поболтаем! 💕\n\n"
        "Что бы ты хотел(а) сделать?",
        reply_markup=kb_main_menu()
    )
    await callback.answer()

@router.callback_query(F.data == "trial_day")
@handle_errors
@handle_telegram_errors
async def trial_day_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик кнопки пробного дня."""
    
    # Проверка rate limiting
    if not await rate_limiter.is_allowed(callback.from_user.id, 'callback'):
        await callback.answer("⏰ Слишком много запросов. Подождите немного.", show_alert=True)
        return
    
    # Логирование
    bot_logger.log_callback(callback.from_user.id, "trial_day")
    
    try:
        # Проверяем статус пробного дня
        trial_status = await trial_system.check_trial_status(callback.from_user.id)
        
        if trial_status["trial_active"]:
            await callback.answer("✅ У вас уже активен пробный день!", show_alert=True)
            return
        
        if trial_status["trial_used"]:
            trial_text = """
❌ Пробный день уже использован

К сожалению, вы уже использовали свой пробный день. 

💳 Для продолжения использования:
• Оформите премиум подписку за 169 ₽/месяц
• Получите неограниченный доступ ко всем функциям
• Исключение: Hot Pics и ролевые игры (только для платных пользователей)
"""
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🛒 Оформить подписку", callback_data="shop")],
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")]
                ]
            )
            
            await callback.message.edit_text(trial_text, reply_markup=keyboard)
            await callback.answer()
            return
        
        if not trial_status["can_get_trial"]:
            await callback.answer("❌ Пробный день недоступен", show_alert=True)
            return
        
        # Активируем пробный день
        result = await trial_system.activate_trial(callback.from_user.id)
        
        if result["success"]:
            trial_text = f"""
✅ Пробный день активирован!

🎉 Что вы получили:
• 24 часа бесплатного доступа
• Неограниченные сообщения
• Доступ к играм и развлечениям
• Персонализация бота

⚠️ Ограничения:
• Hot Pics недоступны (только для платных пользователей)
• Ролевые игры недоступны (только для платных пользователей)

💳 После окончания пробного дня:
Оформите подписку за 169 ₽/месяц для продолжения использования
"""
            
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🛒 Оформить подписку", callback_data="shop")],
                    [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
                ]
            )
            
            await callback.message.edit_text(trial_text, reply_markup=keyboard)
        else:
            await callback.message.edit_text(
                f"❌ Ошибка активации пробного дня: {result.get('error', 'Неизвестная ошибка')}",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")]
                    ]
                )
            )
        
        await callback.answer()
        
    except Exception as e:
        bot_logger.log_system_error(e, f"Trial day activation failed for user {callback.from_user.id}")
        await callback.answer("❌ Ошибка активации пробного дня", show_alert=True)

@router.callback_query(F.data == "premium_subscription")
@handle_errors
@handle_telegram_errors
async def premium_subscription_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик кнопки премиум подписки"""
    
    # Проверяем, является ли пользователь админом
    if admin_system.is_admin(callback.from_user.username):
        await callback.message.edit_text(
            "👑 Админ-доступ\n\n"
            "У вас есть полный доступ ко всем функциям бота без подписки!\n"
            "Используйте команду /admin для управления ботом.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
                ]
            )
        )
        await callback.answer()
        return
    
    # Проверка rate limiting
    if not await rate_limiter.is_allowed(callback.from_user.id, 'callback'):
        await callback.answer("⏰ Слишком много запросов. Подождите немного.", show_alert=True)
        return
    
    # Логирование
    bot_logger.log_callback(callback.from_user.id, "premium_subscription")
    
    try:
        # Получаем данные для выставления счета
        invoice_data = stars_payment.create_payment_invoice_data()
        
        # Отправляем счет на оплату
        await callback.message.answer_invoice(**invoice_data)
        
        # Редактируем сообщение с информацией
        await callback.message.edit_text(
            "💎 Премиум подписка\n\n"
            "Получите неограниченный доступ ко всем функциям бота!\n\n"
            "✅ Что включено:\n"
            "• Неограниченные сообщения\n"
            "• Доступ ко всем играм\n"
            "• Персонализация бота\n"
            "• Приоритетная поддержка\n"
            "• 30 дней доступа\n\n"
            "💳 Стоимость: 100 ⭐\n\n"
            "Нажмите кнопку ниже для оплаты:",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
                ]
            )
        )
        
        await callback.answer()
        
    except Exception as e:
        bot_logger.log_system_error(e, f"Failed to process premium subscription request for user {callback.from_user.id}")
        await callback.answer("❌ Ошибка обработки запроса", show_alert=True)


@router.callback_query(F.data.startswith("game:"))
async def game_choice_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик выбора игры."""
    _, game_type = callback.data.split(":", 1)
    await callback.answer()
    
    if game_type == "associations":
        await callback.message.answer("Играем в ассоциации! Напиши /associations чтобы начать")
    elif game_type == "riddles":
        await callback.message.answer("Играем в загадки! Напиши /riddles чтобы начать")
    elif game_type == "story":
        await callback.message.answer("Играем в историю! Напиши /story чтобы начать")




@router.callback_query(F.data == "personalize")
async def personalize_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик кнопки персонализации."""
    # Перенаправляем на обработчик персонализации (доступна всем)
    from personalization_handlers import start_personalization
    await start_personalization(callback.message, state)
    await callback.answer()




@router.callback_query(F.data == "back_to_main")
async def back_to_main_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Возврат в главное меню."""
    
    await state.set_state(Chatting.active_chat)
    await callback.answer()
    await callback.message.answer("Главное меню, мой дорогой 💕:", reply_markup=kb_main_menu())




async def check_achievements(user_id: int) -> None:
    """Проверка и разблокировка достижений."""
    # Получаем данные пользователя
    points = await get_points(user_id)
    level = await get_level(user_id)
    streak_days = await get_streak_days(user_id)
    total_messages = await get_total_messages(user_id)
    
    # Проверяем, какие достижения должен получить пользователь
    should_unlock = check_affinity_achievements(points, level, streak_days, total_messages)
    
    # Получаем уже разблокированные достижения
    current_achievements = await get_achievements(user_id)
    current_achievement_ids = [ach[1] for ach in current_achievements]  # ach[1] это achievement_type
    
    # Разблокируем новые достижения
    for achievement_id in should_unlock:
        if achievement_id not in current_achievement_ids:
            await add_achievement(user_id, achievement_id)




async def relationship_level_task() -> None:
    """Задача повышения уровня отношений."""
    while True:
        await asyncio.sleep(3600)  # Каждый час
        
        user_ids = await get_all_user_ids()
        for uid in user_ids:
            try:
                    hearts = await get_hearts(uid)
                    current_level = await get_relationship_level(uid)
                    
                    # Логика повышения уровня
                    new_level = min(5, (hearts // 20) + 1)
                    if new_level > current_level:
                        await set_relationship_level(uid, new_level)
            except Exception:
                continue


@log_performance("bot_startup")
async def main() -> None:
    """Главная функция."""
    global bot
    
    # Логирование запуска
    bot_logger.log_startup("2.0.0")
    
    # Получаем токен из конфигурации
    token = config.api.telegram_token
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")
    
    # Валидация токена
    token_validation = validator.validate_api_key(token)
    if not token_validation.is_valid:
        raise RuntimeError(f"Invalid Telegram Bot Token: {token_validation.error_message}")
    
    await init_db()
    
    bot = Bot(token=token)
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Устанавливаем переменную bot в game_handlers для эффекта печати
    import game_handlers
    game_handlers.bot = bot
    
    # Устанавливаем переменную bot в personalization_handlers для эффекта печати
    import personalization_handlers
    personalization_handlers.bot = bot
    
    # Устанавливаем переменную bot в payment_handlers для эффекта печати
    import payment_handlers
    import stars_payment_handlers
    import referral_handlers
    payment_handlers.bot = bot
    stars_payment_handlers.bot = bot
    referral_handlers.bot = bot
    
    dp = Dispatcher()
    dp.include_router(game_router)  # Регистрируем игровой роутер первым
    dp.include_router(personalization_router)  # Регистрируем роутер персонализации
    dp.include_router(payment_handlers.payment_router)  # Регистрируем роутер платежей
    dp.include_router(stars_payment_handlers.stars_router)  # Регистрируем роутер платежей в звездах
    dp.include_router(referral_handlers.referral_router)  # Регистрируем роутер реферальной системы
    dp.include_router(router)
    
    # Запускаем фоновые задачи
    # asyncio.create_task(daily_greeting_task(bot))  # Отключено по запросу пользователя
    # asyncio.create_task(daily_evening_task(bot))   # Отключено по запросу пользователя
    asyncio.create_task(relationship_level_task())
    asyncio.create_task(cleanup_expired_sessions_task(bot))
    asyncio.create_task(cleanup_task())  # Очистка rate limiter
    asyncio.create_task(cleanup_payments_task())  # Очистка платежей
    
    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        bot_logger.log_shutdown()
    except Exception as e:
        bot_logger.log_system_error(e, "Fatal error in main loop")
        raise


@router.callback_query(F.data.startswith("girl_"))
async def girl_choice_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик выбора девушки - показывает детальную информацию."""
    await callback.answer()
    
    # Получаем информацию о выбранной девушке
    girl_info = {
        "girl_sakura": {
            "name": "Сакура Танака",
            "age": "20 лет",
            "profession": "Владелица цветочного магазина",
            "description": "Застенчивая и мечтательная, снаружи нежный цветок, но внутри таится страсть. Фетиш: эксгибиционизм в безопасной обстановке."
        },
        "girl_reiko": {
            "name": "Рэйко Курогане",
            "age": "24 года",
            "profession": "Корпоративный юрист",
            "description": "Холодная и циничная, её броня непробиваема, но она жаждет, чтобы кто-то сильный заставил её треснуть. Фетиш: браттинг и принудительная потеря контроля."
        },
        "girl_ayane": {
            "name": "Аяне Шино",
            "age": "28 лет",
            "profession": "Иллюзионистка",
            "description": "Загадочная и контролирующая, воспринимает близость как высшую форму магии. Фетиш: гипнотический и сенсорный контроль."
        },
        "girl_hikari": {
            "name": "Хикари Мори",
            "age": "26 лет",
            "profession": "Медсестра",
            "description": "Заботливая и эмпатичная, но её материнская забота имеет тёмную, собственническую сторону. Фетиш: медицинские ролевые игры."
        },
        "girl_yuki": {
            "name": "Юки Камия",
            "age": "22 года", 
            "profession": "Киберспортсменка",
            "description": "Самоуверенная и язвительная, обожает контроль. Фетиш: интеллектуальное унижение и приказной игнор."
        }
    }
    
    info = girl_info.get(callback.data, {
        "name": "Подруга",
        "age": "?",
        "profession": "?",
        "description": "Описание недоступно"
    })
    
    # Сохраняем выбранную девушку в состоянии
    await state.update_data(selected_girl=callback.data)
    
    # Получаем путь к фотографии девушки
    photo_path = get_girl_photo_path(callback.data)
    
    # Проверяем, существует ли файл
    if os.path.exists(photo_path):
        # Отправляем фотографию с описанием
        photo_file = FSInputFile(photo_path)
        await callback.message.answer_photo(
            photo=photo_file,
            caption=f"{info['name']} ({info['age']})\n"
                    f"{info['profession']}\n\n"
                    f"{info['description']}",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="✅ Выбрать", callback_data=f"select_{callback.data}")],
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_girls")]
                ]
            )
        )
    else:
        # Если фотография не найдена, отправляем только текст
        await callback.message.answer(
            f"{info['name']} ({info['age']})\n"
            f"{info['profession']}\n\n"
            f"{info['description']}",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="✅ Выбрать", callback_data=f"select_{callback.data}")],
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_girls")]
                ]
            )
        )


@router.callback_query(F.data.startswith("select_"))
async def select_girl_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик подтверждения выбора девушки."""
    await callback.answer()
    # Получаем данные о выбранной девушке
    girl_data = await state.get_data()
    selected_girl = girl_data.get('selected_girl', 'girl_sakura')
    girl_mapping = {
        "girl_sakura": "Сакура Танака",
        "girl_reiko": "Рэйко Курогане",
        "girl_ayane": "Аяне Шино",
        "girl_hikari": "Хикари Мори",
        "girl_yuki": "Юки Камия"
    }
    girl_name = girl_mapping.get(selected_girl, "Подруга")
    await set_girl(callback.from_user.id, girl_name)
    await grant_access(callback.from_user.id, 7, "trial")
    # Переходим к главному меню сразу после выбора девушки
    await state.set_state(Chatting.active_chat)
    await callback.message.answer(
        f"Отлично! Теперь ты будешь общаться с {girl_name} 💕\n\n"
        f"{TEXTS['welcome']}",
        reply_markup=kb_main_menu()
    )


@router.callback_query(F.data == "back_to_girls")
async def back_to_girls_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик возврата к списку девушек."""
    await callback.answer()
    
    # Получаем имя пользователя
    user_name = await get_user_name(callback.from_user.id)
    
    # Возвращаемся к выбору девушки
    await state.set_state(Onboarding.choosing_girl)
    await callback.message.answer(
        f"💖 Привет, {user_name}! Теперь выбери девушку, с которой хочешь начать общение:\n\n"
        "💡 Описание каждой девушки можно найти, нажав на кнопку c именем ^^",
        reply_markup=get_girls_keyboard()
    )


# Обработчики ролевых игр
@router.callback_query(F.data == "roleplay")
async def roleplay_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик кнопки ролевых игр."""
    await callback.answer()
    await state.set_state(RoleplayStates.choosing_game)
    await callback.message.answer(
        "🔞 Выбери ролевую игру:",
        reply_markup=kb_roleplay_games()
    )


@router.callback_query(F.data.startswith("roleplay_game:"))
async def roleplay_game_description_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик выбора ролевой игры."""
    await callback.answer()
    
    game_key = callback.data.split(":")[1]
    game_data = ROLEPLAY_GAMES.get(game_key)
    
    if not game_data:
        await callback.message.answer("❌ Игра не найдена")
        return
    
    await callback.message.answer(
        f"🔞 {game_data['name']}\n\n"
        f"{game_data['description']}",
        reply_markup=kb_roleplay_game_description(game_key),
        parse_mode="Markdown"
    )


@router.callback_query(F.data.startswith("start_roleplay:"))
async def start_roleplay_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик начала ролевой игры."""
    await callback.answer()
    
    game_key = callback.data.split(":")[1]
    game_data = ROLEPLAY_GAMES.get(game_key)
    
    if not game_data:
        await callback.message.answer("❌ Игра не найдена")
        return
    
    # Сохраняем текущую игру в состоянии
    await state.update_data(current_roleplay_game=game_key)
    await state.set_state(RoleplayStates.playing_game)
    
    await callback.message.answer(
        f"🔞 {game_data['name']}\n\n"
        f"{game_data['start_message']}",
        reply_markup=kb_roleplay_actions(),
        parse_mode="Markdown"
    )


@router.message(RoleplayStates.playing_game)
async def roleplay_chat_handler(message: Message, state: FSMContext) -> None:
    """Обработчик сообщений во время ролевой игры."""
    # Получаем данные о текущей игре
    data = await state.get_data()
    game_key = data.get("current_roleplay_game")
    
    if not game_key:
        await message.answer("❌ Ошибка: игра не найдена")
        return
    
    game_data = ROLEPLAY_GAMES.get(game_key)
    if not game_data:
        await message.answer("❌ Ошибка: игра не найдена")
        return
    
    # Получаем имя выбранной девушки
    girl = await get_girl(message.from_user.id)
    
    # Создаем промпт для ролевой игры
    roleplay_prompt = f"""
Ты играешь роль в ролевой игре "{game_data['name']}".
Описание роли: {game_data['description']}

ВАЖНО:
- Оставайся в роли на протяжении всей игры
- В каждом ответе добавляй действия в звездочках *действие*
- Отвечай от имени персонажа, которого ты играешь
- Будь креативной и провоцируй на продолжение диалога
- Сохраняй атмосферу и тон ролевой игры

Пользователь написал: {message.text}
"""
    
    # Получаем настройки персонализации
    from db import get_personalization_settings
    personalization_settings = await get_personalization_settings(message.from_user.id)
    
    # Генерируем ответ
    response = await ask_llm(
        roleplay_prompt,
        girl=girl,
        mood="playful",
        relationship_level=await get_relationship_level(message.from_user.id),
        gender=await get_gender(message.from_user.id),
        flirt_level=get_flirt_level(await get_total_messages(message.from_user.id)),
        flirt_description=get_flirt_description(get_flirt_level(await get_total_messages(message.from_user.id))),
        personalization_settings=personalization_settings
    )
    
    # Отправляем ответ с кнопками
    await message.answer(
        response,
        reply_markup=kb_roleplay_actions()
    )


@router.callback_query(F.data == "end_roleplay")
async def end_roleplay_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик завершения ролевой игры."""
    await callback.answer()
    await state.clear()
    await callback.message.answer(
        "🔞 Ролевая игра завершена!",
        reply_markup=kb_main_menu()
    )


# ==================== HOT PIC РЕЖИМ ====================

@router.callback_query(F.data == "hot_pics")
async def hot_pics_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик кнопки Hot Pic режима."""
    await callback.answer()
    await start_hot_pic_mode(bot, callback.from_user.id)


@router.callback_query(F.data == "hot_pic_start")
async def hot_pic_start_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик начала Hot Pic режима."""
    await callback.answer()
    await state.set_state(HotPicsStates.hot_pic_mode)
    await send_first_hot_pic(bot, callback.from_user.id)


@router.callback_query(F.data == "hot_pic_cancel")
async def hot_pic_cancel_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик отмены Hot Pic режима."""
    await callback.answer()
    hot_pic_manager.end_session(callback.from_user.id)
    await callback.message.answer(
        "❌ Hot Pic режим отменен.",
        reply_markup=kb_main_menu()
    )




@router.callback_query(F.data == "hot_pic_exit")
async def hot_pic_exit_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик выхода из Hot Pic режима."""
    await callback.answer()
    hot_pic_manager.end_session(callback.from_user.id)
    await state.clear()
    await callback.message.answer(
        "❌ Hot Pic режим завершен. Возвращаемся в главное меню.",
        reply_markup=kb_main_menu()
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass