import random
import asyncio
from functools import wraps
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.state import any_state
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ChatAction

from states import GameStates
from game_data import RIDDLES, STORY_PROMPTS
from llm import ask_llm
from db import get_relationship_level, get_gender, get_total_messages, add_hearts
from utils import TEXTS

game_router = Router()

# Глобальная переменная для бота (будет установлена в main.py)
bot = None

def send_typing_action(func):
    """Декоратор для показа эффекта печати перед отправкой ответа."""
    @wraps(func)
    async def wrapper(message: types.Message, *args, **kwargs):
        if bot:
            await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
            await asyncio.sleep(1)  # Небольшая задержка для эффекта
        return await func(message, *args, **kwargs)
    return wrapper


def get_flirt_level(total_messages: int) -> int:
    """Определяет уровень флирта на основе количества сообщений."""
    if total_messages <= 15:
        return 1  # Легкий флирт
    elif total_messages <= 50:
        return 2  # Средний флирт
    else:
        return 3  # Сильный флирт


def get_flirt_description(level: int) -> str:
    """Возвращает описание уровня флирта для промпта."""
    descriptions = {
        1: "Легкий флирт: будь милой и игривой, используй комплименты и легкие намеки. Примеры: 'Ты милый)', 'Мне нравится с тобой говорить', 'Ты такой интересный'",
        2: "Средний флирт: будь более смелой, используй намеки и обсуждай симпатии. Примеры: 'Ты мне начинаешь нравиться все больше...', 'А ты сейчас улыбаешься, когда читаешь это?', 'Ты такой привлекательный'",
        3: "Сильный флирт: будь страстной и романтичной, используй прямые комплименты и романтические фантазии. Примеры: 'Не могу перестать думать о тебе сегодня...', 'Нам бы сейчас встретиться...', 'Ты сводишь меня с ума'"
    }
    return descriptions.get(level, descriptions[1])


# ==================== УНИВЕРСАЛЬНЫЙ ХЕНДЛЕР ВЫХОДА ====================

@game_router.message(Command("stopgame"), any_state)
async def stop_any_game(message: types.Message, state: FSMContext):
    """Универсальный хендлер для выхода из любой игры."""
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Мы и так не играем, котик")
        return

    await state.clear()
    await message.answer("Хорошо, закончили играть. Теперь можем просто поговорить... О чем думаешь?")


# ==================== ИГРА "АССОЦИАЦИИ" ====================

@game_router.message(Command("associations"))
async def start_associations_game(message: types.Message, state: FSMContext):
    """Начало игры в ассоциации."""

    # Список слов для ассоциаций
    words = ["море", "дождь", "солнце", "звезды", "мечта", "любовь", "счастье", "путешествие", "книга", "музыка"]
    first_word = random.choice(words)
    
    await state.set_state(GameStates.associations)
    await state.update_data(current_word=first_word, round=1)
    
    await message.answer(f"Отлично! Давай поиграем в ассоциации. Я загадаю слово, а ты скажи, что у тебя с ним ассоциируется.\n\nПервое слово: {first_word}\n\nКакие у тебя ассоциации, милый?")


@game_router.message(GameStates.associations)
@send_typing_action
async def process_associations_answer(message: types.Message, state: FSMContext):
    """Обработка ответа в игре ассоциации."""
    user_association = message.text.strip()
    game_data = await state.get_data()
    current_word = game_data.get("current_word", "")
    round_num = game_data.get("round", 1)
    
    # Генерируем ответ бота с помощью LLM
    prompt = f"Пользователь дал ассоциацию '{user_association}' к слову '{current_word}'. Ответь как 20-летняя флиртующая девушка. Скажи, что тебе нравится его ассоциация, и предложи свою ассоциацию к этому же слову. Не используй кавычки, говори естественно."
    
    # Получаем настройки персонализации
    from db import get_personalization_settings
    personalization_settings = await get_personalization_settings(message.from_user.id)
    
    response = await ask_llm(
        prompt,
        girl="Подруга",
        mood="playful",
        relationship_level=await get_relationship_level(message.from_user.id),
        gender=await get_gender(message.from_user.id),
        flirt_level=get_flirt_level(await get_total_messages(message.from_user.id)),
        flirt_description=get_flirt_description(get_flirt_level(await get_total_messages(message.from_user.id))),
        personalization_settings=personalization_settings
    )
    
    # Добавляем очки
    await add_hearts(message.from_user.id, 1)
    
    # Создаем кнопки
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Следующая ассоциация", callback_data="next_association")],
        [InlineKeyboardButton(text="Выйти из игры", callback_data="exit_game")]
    ])
    
    await message.answer(response, reply_markup=keyboard)


@game_router.callback_query(F.data == "next_association")
async def next_association_callback(callback: types.CallbackQuery, state: FSMContext):
    """Обработка кнопки 'Следующая ассоциация'."""
    words = ["море", "дождь", "солнце", "звезды", "мечта", "любовь", "счастье", "путешествие", "книга", "музыка", "весна", "осень", "зима", "лето", "утро", "вечер", "ночь", "день"]
    new_word = random.choice(words)
    
    await state.update_data(current_word=new_word)
    
    await callback.message.answer(f"Отлично! Следующее слово: {new_word}\n\nКакие у тебя ассоциации к этому слову?")
    await callback.answer()


# ==================== ИГРА "ЗАГАДКИ" ====================

@game_router.message(Command("riddles"))
async def start_riddles_game(message: types.Message, state: FSMContext):
    """Начало игры в загадки."""

    # Выбираем случайную загадку
    riddle_data = random.choice(RIDDLES)
    riddle_text = riddle_data["question"]
    correct_answer = riddle_data["answer"]
    
    await state.set_state(GameStates.riddles)
    await state.update_data(riddle=riddle_text, answer=correct_answer, attempts=0)
    
    await message.answer(f"Обожаю загадки! Попробуй отгадать мою, умник\n\n{riddle_text}")


@game_router.message(GameStates.riddles)
@send_typing_action
async def process_riddle_answer(message: types.Message, state: FSMContext):
    """Обработка ответа на загадку."""
    user_answer = message.text.lower().strip()
    game_data = await state.get_data()
    correct_answer = game_data.get("answer", "").lower()
    attempts = game_data.get("attempts", 0)
    
    if user_answer == correct_answer:
        # Правильный ответ
        response = "Вау! Правильно! Ты такой сообразительный, мне это безумно нравится!"
        await add_hearts(message.from_user.id, 3)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Следующая загадка", callback_data="next_riddle")],
            [InlineKeyboardButton(text="Выйти из игры", callback_data="exit_game")]
        ])
        
        await message.answer(response, reply_markup=keyboard)
    else:
        # Неправильный ответ
        attempts += 1
        await state.update_data(attempts=attempts)
        
        if attempts < 2:
            response = "Почти угадал! Не сдавайся, попробуй ещё раз, дорогой"
        else:
            response = f"Хи-хи, не угадал! Правильный ответ был: {correct_answer}. Давай в следующий раз повезет!"
            await add_hearts(message.from_user.id, 1)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Подсказка", callback_data="hint_riddle")],
            [InlineKeyboardButton(text="Посмотреть правильный ответ", callback_data="show_answer")],
            [InlineKeyboardButton(text="Следующая загадка", callback_data="next_riddle")],
            [InlineKeyboardButton(text="Выйти из игры", callback_data="exit_game")]
        ])
        
        await message.answer(response, reply_markup=keyboard)


@game_router.callback_query(F.data == "hint_riddle")
async def hint_riddle_callback(callback: types.CallbackQuery, state: FSMContext):
    """Обработка кнопки 'Подсказка'."""
    game_data = await state.get_data()
    riddle_text = game_data.get("riddle", "")
    
    hint_prompt = f"Дай подсказку к загадке: '{riddle_text}'. Подсказка должна быть намеком, но не раскрывать ответ полностью."
    
    # Получаем настройки персонализации
    from db import get_personalization_settings
    personalization_settings = await get_personalization_settings(callback.from_user.id)
    
    hint = await ask_llm(
        hint_prompt,
        girl="Подруга",
        mood="playful",
        relationship_level=await get_relationship_level(callback.from_user.id),
        gender=await get_gender(callback.from_user.id),
        flirt_level=get_flirt_level(await get_total_messages(callback.from_user.id)),
        flirt_description=get_flirt_description(get_flirt_level(await get_total_messages(callback.from_user.id))),
        personalization_settings=personalization_settings
    )
    
    await callback.message.answer(f"Подсказка: {hint}")
    await callback.answer()


@game_router.callback_query(F.data == "show_answer")
async def show_answer_callback(callback: types.CallbackQuery, state: FSMContext):
    """Обработка кнопки 'Посмотреть правильный ответ'."""
    game_data = await state.get_data()
    correct_answer = game_data.get("answer", "")
    
    await callback.message.answer(f"Правильный ответ: {correct_answer}")
    await callback.answer()


@game_router.callback_query(F.data == "next_riddle")
async def next_riddle_callback(callback: types.CallbackQuery, state: FSMContext):
    """Обработка кнопки 'Следующая загадка'."""
    riddle_data = random.choice(RIDDLES)
    riddle_text = riddle_data["question"]
    correct_answer = riddle_data["answer"]
    
    await state.update_data(riddle=riddle_text, answer=correct_answer, attempts=0)
    
    await callback.message.answer(f"Отлично! Следующая загадка:\n\n{riddle_text}")
    await callback.answer()


# ==================== ИГРА "ИСТОРИЯ" ====================

@game_router.message(Command("story"))
async def start_story_game(message: types.Message, state: FSMContext):
    """Начало игры в историю."""

    await state.set_state(GameStates.story)
    await state.update_data(story_parts=[], current_turn="user")
    
    await message.answer("Давай напишем нашу собственную историю страсти... или комедии! Начинай ты, а я продолжу. Жду твое первое предложение...")


@game_router.message(GameStates.story)
@send_typing_action
async def process_story_part(message: types.Message, state: FSMContext):
    """Обработка части истории от пользователя."""
    user_part = message.text.strip()
    game_data = await state.get_data()
    story_parts = game_data.get("story_parts", [])
    current_turn = game_data.get("current_turn", "user")
    
    if current_turn == "user":
        # Добавляем часть пользователя
        story_parts.append(f"Пользователь: {user_part}")
        await state.update_data(story_parts=story_parts, current_turn="bot")
        
        # Генерируем продолжение от бота
        story_text = "\n".join(story_parts)
        prompt = f"Продолжи эту историю (2-3 предложения), сохраняя интригу и добавляя нотки флирта. Вот начало:\n{story_text}\n\nПродолжи как 20-летняя флиртующая девушка:"
        
        # Получаем настройки персонализации
        from db import get_personalization_settings
        personalization_settings = await get_personalization_settings(message.from_user.id)
        
        bot_continuation = await ask_llm(
            prompt,
            girl="Подруга",
            mood="playful",
            relationship_level=await get_relationship_level(message.from_user.id),
            gender=await get_gender(message.from_user.id),
            flirt_level=get_flirt_level(await get_total_messages(message.from_user.id)),
            flirt_description=get_flirt_description(get_flirt_level(await get_total_messages(message.from_user.id))),
            personalization_settings=personalization_settings
        )
        
        story_parts.append(f"Подруга: {bot_continuation}")
        await state.update_data(story_parts=story_parts, current_turn="user")
        
        # Добавляем очки
        await add_hearts(message.from_user.id, 2)
        
        # Создаем кнопки
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Продолжить историю", callback_data="continue_story")],
            [InlineKeyboardButton(text="Завершить историю", callback_data="end_story")],
            [InlineKeyboardButton(text="Выйти из игры", callback_data="exit_game")]
        ])
        
        await message.answer(bot_continuation, reply_markup=keyboard)


@game_router.callback_query(F.data == "continue_story")
async def continue_story_callback(callback: types.CallbackQuery, state: FSMContext):
    """Обработка кнопки 'Продолжить историю'."""
    await state.update_data(current_turn="user")
    await callback.message.answer("Отлично! Теперь твоя очередь продолжить историю. Напиши следующую часть:")
    await callback.answer()


@game_router.callback_query(F.data == "end_story")
async def end_story_callback(callback: types.CallbackQuery, state: FSMContext):
    """Обработка кнопки 'Завершить историю'."""
    game_data = await state.get_data()
    story_parts = game_data.get("story_parts", [])
    
    # Показываем всю историю
    full_story = "\n\n".join(story_parts)
    
    response = "Классная история, мне очень понравилось! Вот что у нас получилось:\n\n" + full_story
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Рассказать новую историю", callback_data="new_story")],
        [InlineKeyboardButton(text="Выйти из игры", callback_data="exit_game")]
    ])
    
    await callback.message.answer(response, reply_markup=keyboard)
    await callback.answer()


@game_router.callback_query(F.data == "new_story")
async def new_story_callback(callback: types.CallbackQuery, state: FSMContext):
    """Обработка кнопки 'Рассказать новую историю'."""
    await state.update_data(story_parts=[], current_turn="user")
    await callback.message.answer("Отлично! Давай напишем новую историю. Начинай ты, а я продолжу. Жду твое первое предложение...")
    await callback.answer()


# ==================== ОБРАБОТЧИК ВЫХОДА ИЗ ИГРЫ ====================

@game_router.callback_query(F.data == "exit_game")
async def exit_game_callback(callback: types.CallbackQuery, state: FSMContext):
    """Обработка кнопки 'Выйти из игры'."""
    await state.clear()
    await callback.message.answer("Хорошо, закончили играть. Теперь можем просто поговорить... О чем думаешь?")
    await callback.answer()