"""
Обработчики для системы персонализации Элизии
"""

import asyncio
from functools import wraps
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ChatAction

from states import PersonalizationStates
from personalization_system import PersonalizationSystem, PersonalityType, CommunicationStyle
from db import get_user_name
from utils import TEXTS

personalization_router = Router()

# Глобальная переменная для бота (будет установлена в main.py)
bot = None

def send_typing_action(func):
    """Декоратор для показа эффекта печати перед отправкой ответа."""
    @wraps(func)
    async def wrapper(message: types.Message, *args, **kwargs):
        if bot:
            await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
            await asyncio.sleep(1)
        return await func(message, *args, **kwargs)
    return wrapper

# Инициализация системы персонализации
personalization_system = PersonalizationSystem()

@personalization_router.message(Command("personalize"))
async def start_personalization(message: types.Message, state: FSMContext):
    """Начало процесса персонализации."""
    await state.set_state(PersonalizationStates.choosing_personality)
    
    text = "🎭 Персонализация Элизии\n\n"
    text += "Привет! Я готова изменить свой характер специально для тебя! 💕\n\n"
    text += "Давай создадим идеальную версию меня, которая будет тебе нравиться больше всего.\n\n"
    text += "Шаг 1/4: Выбери мой основной тип личности:"
    
    # Создаем клавиатуру с типами личности
    keyboard_data = personalization_system.get_personality_keyboard_data()
    buttons = []
    
    for row in keyboard_data:
        button_row = []
        for text, callback_data in row:
            button_row.append(InlineKeyboardButton(text=text, callback_data=callback_data))
        buttons.append(button_row)
    
    # Добавляем кнопку "Назад"
    buttons.append([InlineKeyboardButton(text="⬅️ Главное меню", callback_data="back_to_main")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")

@personalization_router.callback_query(F.data.startswith("personality:"))
async def handle_personality_selection(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора типа личности."""
    personality_name = callback.data.split(":")[1]
    personality = personalization_system.get_personality_by_name(personality_name)
    
    if not personality:
        await callback.answer("Ошибка выбора типа личности")
        return
    
    # Сохраняем выбранный тип личности
    await state.update_data(selected_personality=personality.value)
    
    # Показываем превью
    preview = personalization_system.get_personality_preview(personality)
    
    text = "🎭 Персонализация Элизии\n\n"
    text += f"✅ Выбран тип личности:\n\n{preview}\n\n"
    text += "Шаг 2/4: Теперь выбери, как я буду с тобой общаться:"
    
    # Создаем клавиатуру со стилями общения
    keyboard_data = personalization_system.get_communication_style_keyboard_data()
    buttons = []
    
    for row in keyboard_data:
        button_row = []
        for text, callback_data in row:
            button_row.append(InlineKeyboardButton(text=text, callback_data=callback_data))
        buttons.append(button_row)
    
    # Добавляем кнопки навигации
    buttons.append([
        InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_personality"),
        InlineKeyboardButton(text="➡️ Пропустить", callback_data="skip_style")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await state.set_state(PersonalizationStates.choosing_communication_style)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

@personalization_router.callback_query(F.data.startswith("style:"))
async def handle_communication_style_selection(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора стиля общения."""
    style_name = callback.data.split(":")[1]
    style = personalization_system.get_communication_style_by_name(style_name)
    
    if not style:
        await callback.answer("Ошибка выбора стиля общения")
        return
    
    # Сохраняем выбранный стиль общения
    await state.update_data(selected_communication_style=style.value)
    
    # Показываем превью
    preview = personalization_system.get_communication_style_preview(style)
    
    text = "🎭 Персонализация Элизии\n\n"
    text += f"✅ Выбран стиль общения:\n\n{preview}\n\n"
    text += "Шаг 3/4: Хочешь добавить особые черты характера?\n\n"
    text += "Например:\n"
    text += "• Любит котиков 🐱\n"
    text += "• Увлекается астрономией 🌟\n"
    text += "• Говорит с французским акцентом 🇫🇷\n"
    text += "• Обожает шоколад 🍫\n"
    text += "• Боится пауков 🕷️\n\n"
    text += "Это сделает меня еще более уникальной!"
    
    buttons = [
        [InlineKeyboardButton(text="✏️ Добавить черты", callback_data="add_traits")],
        [InlineKeyboardButton(text="➡️ Пропустить", callback_data="skip_traits")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_style")]
    ]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await state.set_state(PersonalizationStates.custom_traits)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

@personalization_router.callback_query(F.data == "add_traits")
async def handle_add_traits(callback: types.CallbackQuery, state: FSMContext):
    """Обработка добавления дополнительных черт."""
    text = "🎭 Персонализация Элизии\n\n"
    text += "✏️ Дополнительные черты характера\n\n"
    text += "Отлично! Теперь добавь особые черты, которые сделают меня уникальной для тебя.\n\n"
    text += "Примеры:\n"
    text += "• Любит котиков 🐱\n"
    text += "• Увлекается астрономией 🌟\n"
    text += "• Говорит с французским акцентом 🇫🇷\n"
    text += "• Обожает шоколад 🍫\n"
    text += "• Боится пауков 🕷️\n"
    text += "• Коллекционирует марки 📮\n"
    text += "• Играет на пианино 🎹\n\n"
    text += "Напиши свои предложения (каждую черту с новой строки):"
    
    buttons = [
        [InlineKeyboardButton(text="➡️ Пропустить", callback_data="skip_traits")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_style")]
    ]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

@personalization_router.message(PersonalizationStates.custom_traits)
@send_typing_action
async def handle_traits_input(message: types.Message, state: FSMContext):
    """Обработка ввода дополнительных черт."""
    traits_text = message.text.strip()
    
    if not traits_text:
        await message.answer("Пожалуйста, напиши черты характера или нажми 'Пропустить'")
        return
    
    # Разбиваем на отдельные черты
    traits = [t.strip() for t in traits_text.split('\n') if t.strip()]
    
    # Сохраняем черты
    await state.update_data(custom_traits=traits)
    
    text = "🎭 Персонализация Элизии\n\n"
    text += f"✅ Добавлены черты характера:\n\n"
    for trait in traits:
        text += f"• {trait}\n"
    
    text += "\nШаг 4/4: Теперь добавь мои любимые фразы и выражения!\n\n"
    text += "Это фразы, которые я буду часто использовать в общении с тобой:\n\n"
    text += "Примеры:\n"
    text += "• 'Мой дорогой' 💕\n"
    text += "• 'Как же это мило!' ✨\n"
    text += "• 'Ты просто прелесть!' 😊\n"
    text += "• 'О божечки!' 😮\n"
    text += "• 'Это же потрясающе!' 🌟\n\n"
    text += "Напиши свои фразы (каждую с новой строки):"
    
    buttons = [
        [InlineKeyboardButton(text="✏️ Добавить фразы", callback_data="add_phrases")],
        [InlineKeyboardButton(text="➡️ Пропустить", callback_data="skip_phrases")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_traits")]
    ]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await state.set_state(PersonalizationStates.custom_phrases)
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")

@personalization_router.callback_query(F.data == "add_phrases")
async def handle_add_phrases(callback: types.CallbackQuery, state: FSMContext):
    """Обработка добавления любимых фраз."""
    text = "🎭 Персонализация Элизии\n\n"
    text += "💭 Любимые фразы и выражения\n\n"
    text += "Отлично! Теперь добавь фразы, которые я буду часто использовать в общении с тобой.\n\n"
    text += "Примеры:\n"
    text += "• 'Мой дорогой' 💕\n"
    text += "• 'Как же это мило!' ✨\n"
    text += "• 'Ты просто прелесть!' 😊\n"
    text += "• 'О божечки!' 😮\n"
    text += "• 'Это же потрясающе!' 🌟\n"
    text += "• 'Ты меня удивляешь!' 🤩\n"
    text += "• 'Как интересно!' 🤔\n\n"
    text += "Напиши свои фразы (каждую с новой строки):"
    
    buttons = [
        [InlineKeyboardButton(text="➡️ Пропустить", callback_data="skip_phrases")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_traits")]
    ]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

@personalization_router.message(PersonalizationStates.custom_phrases)
@send_typing_action
async def handle_phrases_input(message: types.Message, state: FSMContext):
    """Обработка ввода любимых фраз."""
    phrases_text = message.text.strip()
    
    if not phrases_text:
        await message.answer("Пожалуйста, напиши фразы или нажми 'Пропустить'")
        return
    
    # Разбиваем на отдельные фразы
    phrases = [p.strip() for p in phrases_text.split('\n') if p.strip()]
    
    # Сохраняем фразы
    await state.update_data(custom_phrases=phrases)
    
    # Переходим к подтверждению
    await show_confirmation(message, state)

async def show_confirmation(message: types.Message, state: FSMContext):
    """Показать подтверждение настроек."""
    data = await state.get_data()
    
    personality = personalization_system.get_personality_by_name(data.get('selected_personality', 'sweet'))
    style = personalization_system.get_communication_style_by_name(data.get('selected_communication_style', 'casual'))
    custom_traits = data.get('custom_traits', [])
    custom_phrases = data.get('custom_phrases', [])
    
    if personality and style:
        personality_config = personalization_system.get_personality_config(personality)
        style_config = personalization_system.get_communication_style_config(style)
        
        text = "🎭 Персонализация Элизии\n\n"
        text += "✨ Готово! Вот твоя идеальная Элизия:\n\n"
        
        text += f"👤 Тип личности: {personality_config['name']} {personality_config['emoji']}\n"
        text += f"_{personality_config['description']}_\n\n"
        
        text += f"💬 Стиль общения: {style_config['name']} {style_config['emoji']}\n"
        text += f"_{style_config['description']}_\n\n"
        
        if custom_traits:
            text += f"🌟 Особые черты:\n"
            for trait in custom_traits:
                text += f"• {trait}\n"
            text += "\n"
        
        if custom_phrases:
            text += f"💭 Любимые фразы:\n"
            for phrase in custom_phrases:
                text += f"• {phrase}\n"
            text += "\n"
        
        text += "🎉 Готова стать именно такой, как ты хочешь!\n\n"
        text += "Применить эти настройки?"
        
        buttons = [
            [InlineKeyboardButton(text="✅ Да, применить!", callback_data="apply_personalization")],
            [InlineKeyboardButton(text="✏️ Изменить", callback_data="edit_personalization")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_personalization")]
        ]
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        
        await state.set_state(PersonalizationStates.confirmation)
        await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")

@personalization_router.callback_query(F.data == "apply_personalization")
async def handle_apply_personalization(callback: types.CallbackQuery, state: FSMContext):
    """Применить настройки персонализации."""
    data = await state.get_data()
    
    # Сохраняем настройки в базу данных
    from db import save_personalization_settings
    
    personality_type = data.get('selected_personality', 'sweet')
    communication_style = data.get('selected_communication_style', 'casual')
    custom_traits = data.get('custom_traits', [])
    custom_phrases = data.get('custom_phrases', [])
    
    await save_personalization_settings(
        callback.from_user.id,
        personality_type,
        communication_style,
        custom_traits,
        custom_phrases
    )
    
    text = "🎭 Персонализация Элизии\n\n"
    text += "🎉 Готово! Я изменилась!\n\n"
    text += "Вау! Я чувствую, как мой характер меняется прямо сейчас! ✨\n\n"
    text += "Теперь я буду общаться с тобой именно так, как ты хочешь:\n"
    text += "• С выбранным типом личности 💕\n"
    text += "• В твоем любимом стиле общения 💬\n"
    text += "• С особыми чертами характера 🌟\n"
    text += "• Используя твои любимые фразы 💭\n\n"
    text += "Попробуй написать мне что-нибудь, чтобы увидеть новую меня! 😊\n\n"
    text += "Если захочешь что-то изменить, просто используй команду /personalize"
    
    buttons = [
        [InlineKeyboardButton(text="💬 Начать общение", callback_data="start_chat")],
        [InlineKeyboardButton(text="⬅️ Главное меню", callback_data="back_to_main")]
    ]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await state.clear()
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

# Обработчики кнопок навигации
@personalization_router.callback_query(F.data == "back_to_personality")
async def handle_back_to_personality(callback: types.CallbackQuery, state: FSMContext):
    """Вернуться к выбору типа личности."""
    await state.set_state(PersonalizationStates.choosing_personality)
    
    text = "🎭 **Выбери тип личности**\n\n"
    text += "Какой характер ты хочешь, чтобы у меня был?"
    
    keyboard_data = personalization_system.get_personality_keyboard_data()
    buttons = []
    
    for row in keyboard_data:
        button_row = []
        for text, callback_data in row:
            button_row.append(InlineKeyboardButton(text=text, callback_data=callback_data))
        buttons.append(button_row)
    
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

@personalization_router.callback_query(F.data == "back_to_style")
async def handle_back_to_style(callback: types.CallbackQuery, state: FSMContext):
    """Вернуться к выбору стиля общения."""
    await state.set_state(PersonalizationStates.choosing_communication_style)
    
    text = "💬 **Выбери стиль общения**\n\n"
    text += "Как ты хочешь, чтобы я с тобой общалась?"
    
    keyboard_data = personalization_system.get_communication_style_keyboard_data()
    buttons = []
    
    for row in keyboard_data:
        button_row = []
        for text, callback_data in row:
            button_row.append(InlineKeyboardButton(text=text, callback_data=callback_data))
        buttons.append(button_row)
    
    buttons.append([
        InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_personality"),
        InlineKeyboardButton(text="➡️ Пропустить", callback_data="skip_style")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

@personalization_router.callback_query(F.data == "back_to_traits")
async def handle_back_to_traits(callback: types.CallbackQuery, state: FSMContext):
    """Вернуться к добавлению черт характера."""
    await state.set_state(PersonalizationStates.custom_traits)
    
    text = "✏️ **Дополнительные черты характера**\n\n"
    text += "Напиши черты характера, которые ты хочешь добавить к моей личности.\n"
    text += "Например:\n"
    text += "• Любит котиков\n"
    text += "• Увлекается астрономией\n"
    text += "• Говорит с французским акцентом\n"
    text += "• Обожает шоколад\n"
    text += "• Боится пауков\n\n"
    text += "Напиши свои предложения (каждую черту с новой строки):"
    
    buttons = [
        [InlineKeyboardButton(text="➡️ Пропустить", callback_data="skip_traits")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_style")]
    ]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

# Обработчики пропуска шагов
@personalization_router.callback_query(F.data == "skip_style")
async def handle_skip_style(callback: types.CallbackQuery, state: FSMContext):
    """Пропустить выбор стиля общения."""
    await state.update_data(selected_communication_style="casual")
    await handle_add_traits(callback, state)

@personalization_router.callback_query(F.data == "skip_traits")
async def handle_skip_traits(callback: types.CallbackQuery, state: FSMContext):
    """Пропустить добавление черт характера."""
    await state.update_data(custom_traits=[])
    await handle_add_phrases(callback, state)

@personalization_router.callback_query(F.data == "skip_phrases")
async def handle_skip_phrases(callback: types.CallbackQuery, state: FSMContext):
    """Пропустить добавление фраз."""
    await state.update_data(custom_phrases=[])
    await show_confirmation(callback.message, state)

@personalization_router.callback_query(F.data == "edit_personalization")
async def handle_edit_personalization(callback: types.CallbackQuery, state: FSMContext):
    """Редактировать настройки персонализации."""
    await handle_back_to_personality(callback, state)

@personalization_router.callback_query(F.data == "cancel_personalization")
async def handle_cancel_personalization(callback: types.CallbackQuery, state: FSMContext):
    """Отменить персонализацию."""
    await state.clear()
    await callback.message.edit_text("❌ Персонализация отменена. Ты можешь начать заново с помощью команды /personalize")
    await callback.answer()
