from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Тексты для бота
TEXTS = {
    "welcome": "Привет! Я твоя виртуальная подруга\nЯ так рада тебя видеть! Выбери режим, чтобы мы могли познакомиться поближе) Возможно даже слишком близко...",
    "tariff": "Выбери свой план:",
    "trial": "🎁 Пробный день",
    "ask_name": "Отлично! Как тебя зовут?",
    "ask_gender": "А какой у тебя пол?",
    "choose_girl": "Выбери свою подругу:",
    "genders": [
        ("Мужской", "male"),
        ("Женский", "female")
    ],
    "start_chat": "💌 Начать общение",
    "games": "🎮 Игры",
    "hearts": "❤️ Мои очки",
    "profile": "👤 Профиль",
    "relationships": "💕 Отношения",
    "hot_pics": "🔥 Hot Pics (18+)",
    "back": "⬅️ Назад",
    "hearts_earned": "Получено {amount} ❤️",
    "achievement_unlocked": "🏆 Достижение разблокировано: {name}",
    "relationship_level_up": "Уровень отношений повышен до {level}!",
    "mood_changed": "Настроение изменилось на: {mood}"
}

# Настроения девушек
MOODS = {
    "happy": "Радостная",
    "sad": "Грустная", 
    "playful": "Игривая",
    "caring": "Заботливая",
    "romantic": "Романтичная",
    "shy": "Застенчивая"
}

# Достижения
ACHIEVEMENTS = {
    "first_message": "Первое сообщение",
    "first_heart": "Первое сердце",
    "10_hearts": "10 сердец",
    "50_hearts": "50 сердец",
    "100_hearts": "100 сердец",
    "first_week": "Неделя общения",
    "first_month": "Месяц общения",
    "100_messages": "100 сообщений",
    "500_messages": "500 сообщений",
    "1000_messages": "1000 сообщений",
    "relationship_3": "Уровень отношений 3",
    "relationship_5": "Уровень отношений 5"
}


# Мини-игры
MINI_GAMES = {
    "associations": "🔗 Ассоциации",
    "riddles": "🤔 Загадки", 
    "story": "📖 История"
}

# Ролевые игры
ROLEPLAY_GAMES = {
    "kidnapping": {
        "name": "Похищение сердца",
        "description": "Вы — загадочный незнакомец, который похитил меня, но не для выкупа, а для того, чтобы завоевать мое сердце в уединенном загородном доме.",
        "start_message": "*привязываю тебя к кровати в загородном доме* Ты не бойся... Я не причиню тебе вреда. Я просто хочу, чтобы ты была только моей. *нежно целую твою шею*"
    },
    "boss_secretary": {
        "name": "Строгий босс и непослушная сотрудница",
        "description": "Я ваша личная секретарша, которая осталась после работы, чтобы обсудить годовую премию. Но разговор быстро переходит в нерабочее русло.",
        "start_message": "*закрываю дверь кабинета и поворачиваюсь к тебе* Ну что, мисс... Давай обсудим твою годовую премию. *снимаю пиджак*"
    },
    "doctor_patient": {
        "name": "Врач и пациент",
        "description": "Вы пришли ко мне на особый медицинский осмотр. Я — ваша внимательная и заботливая врач, которая должна провести тщательный, интимный осмотр.",
        "start_message": "*надеваю стерильные перчатки* Добро пожаловать, пациент. Сегодня нам предстоит очень... тщательный осмотр. *приближаюсь к тебе*"
    },
    "nanny_dad": {
        "name": "Няня и папа",
        "description": "Вы — одинокий отец, а я — ваша новая няня. Пока ребенок наконец-то уснул, у нас есть время познакомиться поближе.",
        "start_message": "*тихо закрываю дверь детской* Наконец-то уснул... *поворачиваюсь к тебе с улыбкой* Теперь у нас есть время познакомиться поближе, папа..."
    },
    "elevator_strangers": {
        "name": "Незнакомцы в лифте",
        "description": "Мы с вами застряли в лифте старого офисного здания. Напряжение растет с каждой минутой, а вокруг сгущается тьма.",
        "start_message": "*лифт резко останавливается, свет мигает* О нет... Мы застряли. *прижимаюсь к тебе в темноте* Не бойся, я с тобой..."
    },
    "teacher_student": {
        "name": "Учитель и студентка",
        "description": "Вы остались после уроков для дополнительных занятий. Я — ваша учительница, которая решила, что вы заслуживаете особого поощрения за старания.",
        "start_message": "*закрываю дверь класса* Ты так хорошо учишься... Думаю, ты заслуживаешь особого поощрения. *снимаю очки и приближаюсь*"
    },
    "neighbor_help": {
        "name": "Соседская помощь",
        "description": "Я — ваша соседка, которая пришла одолжить сахар. Но, оказавшись в вашей квартире, понимаю, что мне нужно нечто большее.",
        "start_message": "*стучу в дверь с милой улыбкой* Привет! Можно одолжить сахар? *заглядываю в твою квартиру* Ого, какая уютная..."
    },
    "blind_date": {
        "name": "Свидание вслепую",
        "description": "Мы встретились в баре по предварительной договоренности. Вы — застенчивый парень, а я — девушка, которая взяла на себя инициативу и решила разрядить обстановку.",
        "start_message": "*присаживаюсь рядом с тобой в баре* Привет, застенчивый мальчик... *прикасаюсь к твоей руке* Давай разрядим эту неловкую обстановку..."
    },
    "hotel_maid": {
        "name": "Горничная в отеле",
        "description": "Я пришла убраться в вашем номере люкс, но вижу, что вам требуется совсем другая помощь. Вы — гость, который решил сделать свое пребывание незабываемым.",
        "start_message": "*стучу в дверь номера* Горничная! *вхожу с уборочной тележкой* О, вы еще здесь... Может, вам нужна помощь? *подмигиваю*"
    },
    "beach_seduction": {
        "name": "Соблазнение на пляже",
        "description": "Мы случайно встретились на пустынном ночном пляже. Я — загадочная незнакомка, а вы — парень, который решил составить мне компанию.",
        "start_message": "*сижу на песке под лунным светом* Прекрасная ночь... *поворачиваюсь к тебе* Ты не боишься подойти к незнакомке на пустынном пляже?"
    }
}


def kb_tariff() -> InlineKeyboardMarkup:
    """Клавиатура выбора тарифа."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=TEXTS["trial"], callback_data="trial")],
            [InlineKeyboardButton(text=TEXTS["paid"], callback_data="paid")]
        ]
    )


def kb_gender() -> InlineKeyboardMarkup:
    """Клавиатура выбора пола."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=text, callback_data=f"gender:{code}") 
             for text, code in TEXTS["genders"]]
        ]
    )




def kb_main_menu() -> InlineKeyboardMarkup:
    """Главное меню."""
    from locales import locale_manager
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=locale_manager.get_text("start_chat"), callback_data="start_chat")],
            [InlineKeyboardButton(text=locale_manager.get_text("games"), callback_data="games"),
             InlineKeyboardButton(text=locale_manager.get_text("hearts"), callback_data="hearts")],
            [InlineKeyboardButton(text="🔞 Ролевые игры" if locale_manager.get_language().value == "ru" else "🔞 Roleplay Games", callback_data="roleplay"),
             InlineKeyboardButton(text=locale_manager.get_text("hot_pics"), callback_data="hot_pics")],
            [InlineKeyboardButton(text=locale_manager.get_text("profile"), callback_data="profile"),
             InlineKeyboardButton(text=locale_manager.get_text("relationships"), callback_data="relationships")],
            [InlineKeyboardButton(text="💎 Премиум подписка", callback_data="premium_subscription"),
             InlineKeyboardButton(text="⭐ Пробный день", callback_data="trial_day")],
            [InlineKeyboardButton(text="💰 Зарабатывай вместе с нами", callback_data="referral_system")],
            [InlineKeyboardButton(text="🛒 Магазин", callback_data="shop"),
             InlineKeyboardButton(text=locale_manager.get_text("personalize"), callback_data="personalize")]
        ]
    )




def kb_games() -> InlineKeyboardMarkup:
    """Клавиатура игр."""
    buttons = []
    for i in range(0, len(MINI_GAMES), 2):
        row = []
        for j in range(i, min(i + 2, len(MINI_GAMES))):
            game_key = list(MINI_GAMES.keys())[j]
            text = MINI_GAMES[game_key]
            row.append(InlineKeyboardButton(text=text, callback_data=f"game:{game_key}"))
        buttons.append(row)
    
    buttons.append([InlineKeyboardButton(text=TEXTS["back"], callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def kb_moods() -> InlineKeyboardMarkup:
    """Клавиатура настроений."""
    buttons = []
    for i in range(0, len(MOODS), 2):
        row = []
        for j in range(i, min(i + 2, len(MOODS))):
            mood_key = list(MOODS.keys())[j]
            text = MOODS[mood_key]
            row.append(InlineKeyboardButton(text=text, callback_data=f"mood:{mood_key}"))
        buttons.append(row)
    
    buttons.append([InlineKeyboardButton(text=TEXTS["back"], callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_hearts_emoji(hearts: int) -> str:
    """Получить эмодзи сердец в зависимости от количества."""
    if hearts < 10:
        return "💔"
    elif hearts < 25:
        return "💚"
    elif hearts < 50:
        return "💛"
    elif hearts < 100:
        return "🧡"
    else:
        return "❤️"


def get_relationship_emoji(level: int) -> str:
    """Получить эмодзи уровня отношений."""
    if level == 1:
        return "👋"
    elif level == 2:
        return "😊"
    elif level == 3:
        return "💕"
    elif level == 4:
        return "💖"
    else:
        return "💝"


def format_hearts_message(hearts: int, total_messages: int) -> str:
    """Форматировать сообщение с очками."""
    emoji = get_hearts_emoji(hearts)
    return f"{emoji} Очков симпатии: {hearts}\n💬 Сообщений: {total_messages}"


def format_achievements_message(achievements: list) -> str:
    """Форматировать сообщение с достижениями."""
    if not achievements:
        return "🏆 У тебя пока нет достижений. Общайся со мной, чтобы их получить!"
    
    text = "🏆 Твои достижения:\n\n"
    for achievement in achievements:
        text += f"• {ACHIEVEMENTS.get(achievement, achievement)}\n"
    
    return text




def get_next_achievement(hearts: int, total_messages: int, relationship_level: int) -> str:
    """Получить следующее достижение для разблокировки."""
    if hearts >= 1000 and "1000_hearts" not in [a for a in ACHIEVEMENTS.keys()]:
        return "1000_hearts"
    elif hearts >= 100 and "100_hearts" not in [a for a in ACHIEVEMENTS.keys()]:
        return "100_hearts"
    elif hearts >= 50 and "50_hearts" not in [a for a in ACHIEVEMENTS.keys()]:
        return "50_hearts"
    elif hearts >= 10 and "10_hearts" not in [a for a in ACHIEVEMENTS.keys()]:
        return "10_hearts"
    elif total_messages >= 1000 and "1000_messages" not in [a for a in ACHIEVEMENTS.keys()]:
        return "1000_messages"
    elif total_messages >= 500 and "500_messages" not in [a for a in ACHIEVEMENTS.keys()]:
        return "500_messages"
    elif total_messages >= 100 and "100_messages" not in [a for a in ACHIEVEMENTS.keys()]:
        return "100_messages"
    elif relationship_level >= 5 and "relationship_5" not in [a for a in ACHIEVEMENTS.keys()]:
        return "relationship_5"
    elif relationship_level >= 3 and "relationship_3" not in [a for a in ACHIEVEMENTS.keys()]:
        return "relationship_3"
    
    return None


def kb_roleplay_games() -> InlineKeyboardMarkup:
    """Клавиатура выбора ролевых игр."""
    buttons = []
    games = list(ROLEPLAY_GAMES.items())
    
    for i in range(0, len(games), 2):
        row = []
        for j in range(i, min(i + 2, len(games))):
            game_key, game_data = games[j]
            text = game_data["name"]
            row.append(InlineKeyboardButton(text=text, callback_data=f"roleplay_game:{game_key}"))
        buttons.append(row)
    
    # Добавляем кнопку "Назад"
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def kb_roleplay_game_description(game_key: str) -> InlineKeyboardMarkup:
    """Клавиатура для описания ролевой игры."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎮 Играть", callback_data=f"start_roleplay:{game_key}")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="roleplay")]
        ]
    )


def kb_roleplay_actions() -> InlineKeyboardMarkup:
    """Клавиатура действий во время ролевой игры."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛑 Закончить игру", callback_data="end_roleplay")],
            [InlineKeyboardButton(text="🔄 Сменить игру", callback_data="roleplay")]
        ]
    )


def get_girl_photo_path(girl_key: str) -> str:
    """Получает путь к фотографии девушки."""
    import os
    
    # Маппинг ключей девушек к именам папок
    girl_folder_mapping = {
        "girl_sakura": "sakura tanaka",
        "girl_reiko": "reiko kurogane", 
        "girl_ayane": "ayane shino",
        "girl_hikari": "hikari mori",
        "girl_yuki": "uki kamia"
    }
    
    # Маппинг ключей девушек к именам файлов
    girl_file_mapping = {
        "girl_sakura": "s1.png",
        "girl_reiko": "r1.png",
        "girl_ayane": "a1.png", 
        "girl_hikari": "h1.png",
        "girl_yuki": "u1.png"
    }
    
    folder_name = girl_folder_mapping.get(girl_key, "sakura tanaka")
    file_name = girl_file_mapping.get(girl_key, "s1.png")
    
    # Путь к папке с фотографиями
    base_path = os.path.dirname(os.path.abspath(__file__))
    photo_path = os.path.join(base_path, "girls pic", folder_name, file_name)
    
    return photo_path