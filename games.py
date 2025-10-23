from __future__ import annotations

import random
from typing import Dict, List, Tuple, Optional

# Данные для игр
ASSOCIATIONS = [
    "море", "солнце", "звезды", "дождь", "снег", "цветы", "кофе", "чай", 
    "книга", "музыка", "танцы", "путешествия", "мечты", "счастье", "любовь",
    "дружба", "семья", "дом", "работа", "отдых", "спорт", "искусство",
    "природа", "животные", "еда", "время", "память", "будущее", "прошлое"
]

RIDDLES = [
    {
        "question": "Что можно сломать, не держа в руках?",
        "answer": "обещание",
        "hints": ["Это связано с словами", "Можно дать и не сдержать"]
    },
    {
        "question": "Что всегда впереди нас, но мы его никогда не видим?",
        "answer": "будущее",
        "hints": ["Это время", "Оно всегда грядёт"]
    },
    {
        "question": "Что можно слышать, но нельзя увидеть?",
        "answer": "звук",
        "hints": ["Это физическое явление", "Его можно почувствовать"]
    },
    {
        "question": "Что становится мокрым, когда сохнет?",
        "answer": "полотенце",
        "hints": ["Это предмет в ванной", "Им вытираются"]
    },
    {
        "question": "Что можно сломать, не прикасаясь к нему?",
        "answer": "сердце",
        "hints": ["Это орган", "Можно разбить словами"]
    }
]

COMPLIMENTS = {
    "male": [
        "Ты такой сильный и мужественный! 💪",
        "У тебя такой красивый голос! 😍",
        "Ты такой умный и рассудительный! 🧠",
        "У тебя такие добрые глаза! 👀",
        "Ты такой заботливый и внимательный! 💕",
        "У тебя такая красивая улыбка! 😊",
        "Ты такой талантливый и креативный! 🎨",
        "У тебя такое обаяние! 😘",
        "Ты такой надёжный и верный! 🤝",
        "У тебя такая красивая душа! ✨"
    ],
    "female": [
        "Ты такая красивая и элегантная! 💄",
        "У тебя такие выразительные глаза! 👁️",
        "Ты такая умная и мудрая! 🧠",
        "У тебя такая очаровательная улыбка! 😊",
        "Ты такая нежная и заботливая! 💕",
        "У тебя такая красивая душа! ✨",
        "Ты такая талантливая и креативная! 🎨",
        "У тебя такое обаяние! 😘",
        "Ты такая сильная и независимая! 💪",
        "У тебя такая красивая энергия! ⚡"
    ]
}

TRUTH_QUESTIONS = {
    "male": [
        "Какая твоя самая большая мечта?",
        "Что тебя больше всего вдохновляет?",
        "Какой твой самый смешной поступок?",
        "Что ты больше всего ценишь в людях?",
        "Какая твоя самая большая слабость?",
        "Что тебя больше всего пугает?",
        "Какой твой идеальный день?",
        "Что ты больше всего хочешь изменить в себе?",
        "Какая твоя самая большая гордость?",
        "Что тебя больше всего расслабляет?"
    ],
    "female": [
        "Какая твоя самая большая мечта?",
        "Что тебя больше всего вдохновляет?",
        "Какой твой самый смешной поступок?",
        "Что ты больше всего ценишь в людях?",
        "Какая твоя самая большая слабость?",
        "Что тебя больше всего пугает?",
        "Какой твой идеальный день?",
        "Что ты больше всего хочешь изменить в себе?",
        "Какая твоя самая большая гордость?",
        "Что тебя больше всего расслабляет?"
    ]
}

DARE_TASKS = [
    "Спой мне песню! 🎵",
    "Расскажи анекдот! 😄",
    "Сделай комплимент себе! 😊",
    "Расскажи о своей мечте! ✨",
    "Сделай зарядку! 💪",
    "Расскажи стихотворение! 📝",
    "Сделай смешное лицо! 😜",
    "Расскажи о своём хобби! 🎨",
    "Сделай танец! 💃",
    "Расскажи о своём любимом фильме! 🎬"
]

# Состояния игр для каждого пользователя
game_states: Dict[int, Dict] = {}

# История ответов пользователей для персонализации
user_responses: Dict[int, List[str]] = {}

def get_game_state(user_id: int) -> Dict:
    """Получить состояние игры для пользователя."""
    if user_id not in game_states:
        game_states[user_id] = {
            "current_game": None,
            "game_data": {},
            "score": 0
        }
    return game_states[user_id]

def save_user_response(user_id: int, response: str) -> None:
    """Сохранить ответ пользователя для персонализации."""
    if user_id not in user_responses:
        user_responses[user_id] = []
    user_responses[user_id].append(response)
    # Ограничиваем историю последними 10 ответами
    if len(user_responses[user_id]) > 10:
        user_responses[user_id] = user_responses[user_id][-10:]

def get_personalized_response(user_id: int, base_responses: List[str]) -> str:
    """Получить персонализированный ответ на основе истории пользователя."""
    if user_id not in user_responses or not user_responses[user_id]:
        return random.choice(base_responses)
    
    # Анализируем последние ответы пользователя
    recent_responses = user_responses[user_id][-3:]  # Последние 3 ответа
    response_text = " ".join(recent_responses).lower()
    
    # Персонализируем ответы на основе стиля пользователя
    if any(word in response_text for word in ["круто", "классно", "супер", "отлично"]):
        # Пользователь использует позитивные слова
        personalized_responses = [
            f"Мне нравится твой позитивный настрой! {random.choice(base_responses)}",
            f"Ты такой оптимистичный! {random.choice(base_responses)}",
            f"Твоя энергия заразительна! {random.choice(base_responses)}"
        ]
    elif any(word in response_text for word in ["грустно", "печально", "устал", "сложно"]):
        # Пользователь выражает грусть
        personalized_responses = [
            f"Понимаю, что тебе нелегко, но ты справишься! {random.choice(base_responses)}",
            f"Ты такой сильный, что преодолеешь любые трудности! {random.choice(base_responses)}",
            f"Я верю в тебя! {random.choice(base_responses)}"
        ]
    elif any(word in response_text for word in ["люблю", "нравится", "обожаю", "восхищаюсь"]):
        # Пользователь выражает любовь
        personalized_responses = [
            f"Ты такой романтичный! {random.choice(base_responses)}",
            f"Мне нравится, как ты выражаешь чувства! {random.choice(base_responses)}",
            f"Ты такой нежный! {random.choice(base_responses)}"
        ]
    elif len(response_text.split()) > 10:
        # Пользователь дает развернутые ответы
        personalized_responses = [
            f"Ты такой красноречивый! {random.choice(base_responses)}",
            f"Мне нравится, как ты подробно отвечаешь! {random.choice(base_responses)}",
            f"Ты такой интересный собеседник! {random.choice(base_responses)}"
        ]
    else:
        # Обычные ответы
        personalized_responses = base_responses
    
    return random.choice(personalized_responses)

def start_associations(user_id: int) -> str:
    """Начать игру в ассоциации."""
    state = get_game_state(user_id)
    state["current_game"] = "associations"
    state["game_data"] = {
        "current_word": random.choice(ASSOCIATIONS),
        "round": 1,
        "total_rounds": 5
    }
    
    
    return f"🔗 Игра в ассоциации! Я скажу слово, а ты скажи первое, что приходит в голову 😘\n\nСлово #{state['game_data']['round']}: '{state['game_data']['current_word']}'"

def process_association(user_id: int, user_response: str) -> str:
    """Обработать ответ в игре ассоциаций."""
    state = get_game_state(user_id)
    if state["current_game"] != "associations":
        return "Мы не играем в ассоциации сейчас 😊"
    
    # Сохраняем ответ пользователя
    save_user_response(user_id, user_response)
    
    game_data = state["game_data"]
    base_responses = [
        f"Интересно! '{user_response}' - хорошая ассоциация с '{game_data['current_word']}' 😊",
        f"Мне нравится твоя ассоциация! '{user_response}' действительно подходит к '{game_data['current_word']}' 💕",
        f"Отлично! '{user_response}' - очень творческая ассоциация с '{game_data['current_word']}' 😘",
        f"Классно! '{user_response}' - неожиданная ассоциация с '{game_data['current_word']}' 💖",
        f"Здорово! '{user_response}' - красивая ассоциация с '{game_data['current_word']}' 😍"
    ]
    
    # Получаем персонализированный ответ
    response = get_personalized_response(user_id, base_responses)
    state["score"] += 1
    
    # Переходим к следующему слову
    game_data["round"] += 1
    if game_data["round"] <= game_data["total_rounds"]:
        game_data["current_word"] = random.choice(ASSOCIATIONS)
        response += f"\n\nСлово #{game_data['round']}: '{game_data['current_word']}'"
    else:
        # Игра окончена
        response += f"\n\n🎉 Игра окончена! Ты набрал {state['score']} очков! Ты такой умный! 😘"
        state["current_game"] = None
        state["game_data"] = {}
        state["score"] = 0
    
    return response

def start_riddles(user_id: int) -> str:
    """Начать игру в загадки."""
    state = get_game_state(user_id)
    state["current_game"] = "riddles"
    state["game_data"] = {
        "current_riddle": random.choice(RIDDLES),
        "round": 1,
        "total_rounds": 3,
        "hints_used": 0
    }
    
    return f"🤔 Загадка #{state['game_data']['round']}:\n{state['game_data']['current_riddle']['question']}\n\nПопробуй отгадать! Если не получается, скажи 'подсказка' 😘"

def process_riddle(user_id: int, user_response: str) -> str:
    """Обработать ответ в игре загадок."""
    state = get_game_state(user_id)
    if state["current_game"] != "riddles":
        return "Мы не играем в загадки сейчас 😊"
    
    # Сохраняем ответ пользователя
    save_user_response(user_id, user_response)
    
    game_data = state["game_data"]
    current_riddle = game_data["current_riddle"]
    
    if user_response.lower() == "подсказка":
        if game_data["hints_used"] < len(current_riddle["hints"]):
            hint = current_riddle["hints"][game_data["hints_used"]]
            game_data["hints_used"] += 1
            return f"💡 Подсказка: {hint}\n\nПопробуй ещё раз! 😊"
        else:
            return f"😅 Подсказки закончились! Правильный ответ: '{current_riddle['answer']}'\n\nПереходим к следующей загадке! 😘"
    
    # Проверяем ответ (более гибкая проверка)
    user_answer = user_response.lower().strip()
    correct_answer = current_riddle["answer"].lower()
    
    # Проверяем точное совпадение или частичное
    if (user_answer == correct_answer or 
        user_answer in correct_answer or 
        correct_answer in user_answer or
        any(word in user_answer for word in correct_answer.split())):
        # Правильный ответ
        state["score"] += 1
        base_responses = [
            f"🎉 Правильно! Ты такой умный! '{current_riddle['answer']}' - верный ответ! 😍",
            f"🌟 Отлично! Ты отгадал! '{current_riddle['answer']}' - именно это! 💕",
            f"🎯 Браво! Ты такой сообразительный! '{current_riddle['answer']}' - правильно! 😘",
            f"🏆 Превосходно! Ты такой умный! '{current_riddle['answer']}' - верно! 💖"
        ]
        response = get_personalized_response(user_id, base_responses)
    else:
        # Неправильный ответ
        base_responses = [
            f"😊 Не совсем так, но ты молодец, что пытаешься! Попробуй ещё раз 💕",
            f"🤔 Почти, но не то! Не сдавайся, попробуй ещё раз 😘",
            f"💭 Интересная мысль, но не совсем! Давай попробуем ещё раз 💖",
            f"😊 Хорошая попытка! Но ответ другой, попробуй ещё раз 😍"
        ]
        response = get_personalized_response(user_id, base_responses)
    
    # Переходим к следующей загадке
    game_data["round"] += 1
    if game_data["round"] <= game_data["total_rounds"]:
        game_data["current_riddle"] = random.choice(RIDDLES)
        game_data["hints_used"] = 0
        response += f"\n\n🤔 Загадка #{game_data['round']}:\n{game_data['current_riddle']['question']}\n\nПопробуй отгадать! Если не получается, скажи 'подсказка' 😘"
    else:
        # Игра окончена
        response += f"\n\n🎉 Игра окончена! Ты отгадал {state['score']} загадок! Ты такой умный! 😘"
        state["current_game"] = None
        state["game_data"] = {}
        state["score"] = 0
    
    return response

def start_compliments(user_id: int, gender: str) -> str:
    """Начать игру в комплименты."""
    state = get_game_state(user_id)
    state["current_game"] = "compliments"
    state["game_data"] = {
        "round": 1,
        "total_rounds": 5,
        "gender": gender
    }
    
    return f"💕 Игра в комплименты! Скажи мне комплимент, а я отвечу тебе тем же 😊\n\nРаунд {state['game_data']['round']}/{state['game_data']['total_rounds']}\n\nНачни с комплимента! 😘"

def process_compliment(user_id: int, user_compliment: str) -> str:
    """Обработать комплимент в игре комплиментов."""
    state = get_game_state(user_id)
    if state["current_game"] != "compliments":
        return "Мы не играем в комплименты сейчас 😊"
    
    # Сохраняем ответ пользователя
    save_user_response(user_id, user_compliment)
    
    game_data = state["game_data"]
    gender = game_data["gender"]
    
    # Выбираем комплимент в ответ
    compliment = random.choice(COMPLIMENTS.get(gender, COMPLIMENTS["male"]))
    
    base_responses = [
        f"Спасибо за твой комплимент! {compliment}",
        f"Как мило! {compliment}",
        f"Ты такой добрый! {compliment}",
        f"Спасибо! {compliment}",
        f"Как приятно! {compliment}"
    ]
    
    # Получаем персонализированный ответ
    response = get_personalized_response(user_id, base_responses)
    state["score"] += 1
    
    # Переходим к следующему раунду
    game_data["round"] += 1
    if game_data["round"] <= game_data["total_rounds"]:
        response += f"\n\nРаунд {game_data['round']}/{game_data['total_rounds']}\n\nСкажи мне ещё один комплимент! 😘"
    else:
        # Игра окончена
        response += f"\n\n🎉 Игра окончена! Мы обменялись {state['score']} комплиментами! Ты такой милый! 😘"
        state["current_game"] = None
        state["game_data"] = {}
        state["score"] = 0
    
    return response

def start_truth_dare(user_id: int, gender: str) -> str:
    """Начать игру правда или действие."""
    state = get_game_state(user_id)
    state["current_game"] = "truth_dare"
    state["game_data"] = {
        "round": 1,
        "total_rounds": 5,
        "gender": gender
    }
    
    return f"🎯 Правда или действие! Выбирай, что хочешь: 'правда' или 'действие' 😘\n\nРаунд {state['game_data']['round']}/{state['game_data']['total_rounds']}"

def process_truth_dare(user_id: int, user_choice: str) -> str:
    """Обработать выбор в игре правда или действие."""
    state = get_game_state(user_id)
    if state["current_game"] != "truth_dare":
        return "Мы не играем в правда или действие сейчас 😊"
    
    # Сохраняем ответ пользователя
    save_user_response(user_id, user_choice)
    
    game_data = state["game_data"]
    gender = game_data["gender"]
    
    if user_choice.lower() in ["правда", "truth"]:
        # Правда
        question = random.choice(TRUTH_QUESTIONS.get(gender, TRUTH_QUESTIONS["male"]))
        base_responses = [
            f"💭 Правда! Отвечай честно: {question} 😊",
            f"🤔 Интересно! Правда: {question} 💕",
            f"💭 Честно говоря: {question} 😘"
        ]
        response = get_personalized_response(user_id, base_responses)
    elif user_choice.lower() in ["действие", "dare", "действие"]:
        # Действие
        task = random.choice(DARE_TASKS)
        base_responses = [
            f"🎬 Действие! Выполни это: {task} 😘",
            f"🎯 Вызов принят! {task} 💕",
            f"🎪 Покажи, на что способен! {task} 😊"
        ]
        response = get_personalized_response(user_id, base_responses)
    else:
        base_responses = [
            "😊 Выбери 'правда' или 'действие'! 😘",
            "🤔 Что выберешь: правда или действие? 💕",
            "😊 Правда или действие? Решай! 😘"
        ]
        response = get_personalized_response(user_id, base_responses)
        return response
    
    state["score"] += 1
    
    # Переходим к следующему раунду
    game_data["round"] += 1
    if game_data["round"] <= game_data["total_rounds"]:
        response += f"\n\nРаунд {game_data['round']}/{game_data['total_rounds']}\n\nВыбирай снова: 'правда' или 'действие'! 😘"
    else:
        # Игра окончена
        response += f"\n\n🎉 Игра окончена! Мы прошли {state['score']} раундов! Ты такой смелый! 😘"
        state["current_game"] = None
        state["game_data"] = {}
        state["score"] = 0
    
    return response

def process_game_message(user_id: int, message: str, gender: str = "male") -> str:
    """Обработать сообщение в контексте игры."""
    state = get_game_state(user_id)
    
    
    if not state["current_game"]:
        return "Мы не играем в игру сейчас 😊"
    
    if state["current_game"] == "associations":
        return process_association(user_id, message)
    elif state["current_game"] == "riddles":
        return process_riddle(user_id, message)
    elif state["current_game"] == "compliments":
        return process_compliment(user_id, message)
    elif state["current_game"] == "truth_dare":
        return process_truth_dare(user_id, message)
    elif state["current_game"] == "story":
        return process_story(user_id, message)
    else:
        return "Мы не играем в игру сейчас 😊"

def start_story(user_id: int) -> str:
    """Начать игру в историю."""
    state = get_game_state(user_id)
    state["current_game"] = "story"
    state["game_data"] = {
        "story_parts": [],
        "round": 1,
        "total_rounds": 5
    }
    
    return f"📖 Игра в историю! Давай сочиним историю вместе! 😘\n\nРаунд {state['game_data']['round']}/{state['game_data']['total_rounds']}\n\nНачни предложение, а я продолжу! 💕"

def process_story(user_id: int, user_text: str) -> str:
    """Обработать ответ в игре истории."""
    state = get_game_state(user_id)
    if state["current_game"] != "story":
        return "Мы не играем в историю сейчас 😊"
    
    # Сохраняем ответ пользователя
    save_user_response(user_id, user_text)
    
    game_data = state["game_data"]
    
    # Добавляем часть пользователя
    game_data["story_parts"].append(f"Пользователь: {user_text}")
    
    # Генерируем продолжение на основе стиля пользователя
    story_continuations = [
        f"И вдруг произошло что-то неожиданное...",
        f"В этот момент он понял, что всё изменилось...",
        f"Но тут появился кто-то, кто всё перевернул...",
        f"Внезапно раздался звук, который изменил всё...",
        f"И тогда он решил, что пора действовать...",
        f"Но судьба приготовила ему сюрприз...",
        f"В этот момент всё стало ясно...",
        f"И он понял, что это только начало..."
    ]
    
    # Персонализируем продолжение на основе стиля пользователя
    if user_id in user_responses and user_responses[user_id]:
        recent_responses = " ".join(user_responses[user_id][-2:]).lower()
        if any(word in recent_responses for word in ["романтично", "любовь", "сердце", "чувства"]):
            story_continuations = [
                f"И в этот момент их сердца забились в унисон...",
                f"Взгляд их встретился, и время остановилось...",
                f"Она поняла, что это была судьба...",
                f"И тогда он признался ей в любви..."
            ]
        elif any(word in recent_responses for word in ["страшно", "ужас", "монстр", "тень"]):
            story_continuations = [
                f"Внезапно из тени появилась фигура...",
                f"Странный звук заставил его обернуться...",
                f"Он понял, что не один в этом месте...",
                f"Что-то зловещее приближалось..."
            ]
        elif any(word in recent_responses for word in ["смешно", "весело", "смех", "шутка"]):
            story_continuations = [
                f"И тут произошло нечто совершенно нелепое...",
                f"Он не мог сдержать смех...",
                f"Ситуация стала настолько абсурдной...",
                f"И тогда все начали смеяться..."
            ]
    
    continuation = random.choice(story_continuations)
    game_data["story_parts"].append(f"Подруга: {continuation}")
    
    response = f"💭 {continuation}\n\n"
    state["score"] += 1
    
    # Переходим к следующему раунду
    game_data["round"] += 1
    if game_data["round"] <= game_data["total_rounds"]:
        response += f"Раунд {game_data['round']}/{game_data['total_rounds']}\n\nПродолжай историю! 😘"
    else:
        # Игра окончена
        story_text = "\n".join(game_data["story_parts"])
        response += f"🎉 История готова! Мы написали {state['score']} частей! 😍\n\n📖 Наша история:\n{story_text}\n\nТы такой творческий! 💕"
        state["current_game"] = None
        state["game_data"] = {}
        state["score"] = 0
    
    return response

def end_current_game(user_id: int) -> str:
    """Завершить текущую игру."""
    state = get_game_state(user_id)
    if state["current_game"]:
        game_name = state["current_game"]
        state["current_game"] = None
        state["game_data"] = {}
        state["score"] = 0
        return f"Игра '{game_name}' завершена! Возвращаемся в главное меню 😊"
    return "Мы не играем в игру сейчас 😊"
