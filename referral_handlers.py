"""
Обработчики для реферальной системы
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

from logger import bot_logger
from error_handler import handle_errors, handle_telegram_errors
from referral_system import referral_system
from db import process_referral, has_referrer

referral_router = Router()

@referral_router.callback_query(F.data == "referral_system")
@handle_errors
@handle_telegram_errors
async def referral_system_handler(callback: CallbackQuery) -> None:
    """Обработчик кнопки реферальной системы"""
    user_id = callback.from_user.id
    
    # Логирование
    bot_logger.log_command(user_id, "referral_system")
    
    try:
        # Получаем информацию о рефералах
        referral_info = await referral_system.get_referral_info(user_id)
        
        # Создаем клавиатуру
        keyboard = await referral_system.create_referral_keyboard(user_id)
        
        # Отправляем сообщение
        await callback.message.edit_text(
            await referral_system.get_referral_stats_text(user_id),
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
        await callback.answer()
        
    except Exception as e:
        bot_logger.log_system_error(e, f"Failed to show referral system for user {user_id}")
        await callback.answer("❌ Ошибка загрузки реферальной системы", show_alert=True)

@referral_router.callback_query(F.data == "referral_stats")
@handle_errors
@handle_telegram_errors
async def referral_stats_handler(callback: CallbackQuery) -> None:
    """Обработчик статистики рефералов"""
    user_id = callback.from_user.id
    
    try:
        # Получаем статистику
        stats_text = await referral_system.get_referral_stats_text(user_id)
        keyboard = await referral_system.create_referral_keyboard(user_id)
        
        await callback.message.edit_text(
            stats_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
        await callback.answer()
        
    except Exception as e:
        bot_logger.log_system_error(e, f"Failed to show referral stats for user {user_id}")
        await callback.answer("❌ Ошибка загрузки статистики", show_alert=True)

@referral_router.callback_query(F.data == "copy_referral_link")
@handle_errors
@handle_telegram_errors
async def copy_referral_link_handler(callback: CallbackQuery) -> None:
    """Обработчик копирования реферальной ссылки"""
    user_id = callback.from_user.id
    
    try:
        # Получаем реферальную ссылку
        referral_info = await referral_system.get_referral_info(user_id)
        referral_link = referral_info['link']
        
        # Создаем клавиатуру с кнопкой "Назад"
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="referral_system")]
            ]
        )
        
        await callback.message.edit_text(
            f"🔗 Твоя реферальная ссылка:\n\n"
            f"`{referral_link}`\n\n"
            f"💡 Скопируй эту ссылку и поделись с друзьями!\n"
            f"💰 За каждого друга, который оформит подписку, ты получишь {referral_system.COMMISSION_RATE * 100}% от стоимости подписки!",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
        await callback.answer("✅ Ссылка готова к копированию!")
        
    except Exception as e:
        bot_logger.log_system_error(e, f"Failed to copy referral link for user {user_id}")
        await callback.answer("❌ Ошибка получения ссылки", show_alert=True)

@referral_router.callback_query(F.data == "referral_leaderboard")
@handle_errors
@handle_telegram_errors
async def referral_leaderboard_handler(callback: CallbackQuery) -> None:
    """Обработчик топа рефереров"""
    user_id = callback.from_user.id
    
    try:
        # Получаем топ рефереров
        leaderboard_text = await referral_system.get_leaderboard_text()
        
        # Создаем клавиатуру с кнопкой "Назад"
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="referral_system")]
            ]
        )
        
        await callback.message.edit_text(
            leaderboard_text,
            reply_markup=keyboard
        )
        
        await callback.answer()
        
    except Exception as e:
        bot_logger.log_system_error(e, f"Failed to show leaderboard for user {user_id}")
        await callback.answer("❌ Ошибка загрузки топа", show_alert=True)

@referral_router.callback_query(F.data == "referral_help")
@handle_errors
@handle_telegram_errors
async def referral_help_handler(callback: CallbackQuery) -> None:
    """Обработчик помощи по реферальной системе"""
    user_id = callback.from_user.id
    
    try:
        # Получаем текст помощи
        help_text = await referral_system.get_help_text()
        
        # Создаем клавиатуру с кнопкой "Назад"
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="referral_system")]
            ]
        )
        
        await callback.message.edit_text(
            help_text,
            reply_markup=keyboard
        )
        
        await callback.answer()
        
    except Exception as e:
        bot_logger.log_system_error(e, f"Failed to show referral help for user {user_id}")
        await callback.answer("❌ Ошибка загрузки помощи", show_alert=True)

@referral_router.message(Command("referral"))
@handle_errors
@handle_telegram_errors
async def referral_command_handler(message: Message) -> None:
    """Обработчик команды /referral"""
    user_id = message.from_user.id
    
    # Логирование
    bot_logger.log_command(user_id, "referral")
    
    try:
        # Получаем информацию о рефералах
        referral_info = await referral_system.get_referral_info(user_id)
        
        # Создаем клавиатуру
        keyboard = await referral_system.create_referral_keyboard(user_id)
        
        # Отправляем сообщение
        await message.answer(
            await referral_system.get_referral_stats_text(user_id),
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        bot_logger.log_system_error(e, f"Failed to process referral command for user {user_id}")
        await message.answer("❌ Ошибка загрузки реферальной системы")
