"""
Система Hot Pic режима для Telegram бота "Виртуальная подруга"
Реализует возбуждающий режим общения с отправкой фотографий
"""

import os
import random
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Set, Optional
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import Bot
from db import get_girl

class HotPicMode:
    """Класс для управления режимом Hot Pic"""
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.selected_girl = None
        self.sent_photos = set()
        self.session_start = datetime.now()
        self.last_activity = datetime.now()
        self.is_active = True
        self.message_count = 0  # Счетчик сообщений в сессии
        self.last_photo_time = None  # Время последней отправленной фотографии
        
        # Маппинг девушек на папки с фотографиями
        self.available_girls = {
            'Сакура Танака': 'girls pic/sakura tanaka/',
            'Хикари Мори': 'girls pic/hikari mori/',
            'Рэйко Курогане': 'girls pic/reiko kurogane/',
            'Аяне Шино': 'girls pic/ayane shino/',
            'Юки Камия': 'girls pic/uki kamia/'
        }
        
        # Фотографии, которые не отправляются в первую очередь
        self.excluded_first = {'a1.png', 'h1.png', 'r1.png', 's1.png', 'u1.png'}
    
    async def initialize(self):
        """Инициализация режима - получение выбранной девушки"""
        self.selected_girl = await get_girl(self.user_id)
        if not self.selected_girl:
            self.selected_girl = 'Сакура Танака'  # По умолчанию
    
    def get_random_photo(self) -> Optional[str]:
        """Получает случайную фотографию выбранной девушки"""
        if not self.selected_girl:
            return None
            
        girl_folder = self.available_girls.get(self.selected_girl)
        if not girl_folder:
            return None
            
        # Проверяем существование папки
        if not os.path.exists(girl_folder):
            return None
            
        # Получаем все PNG файлы
        all_photos = [f for f in os.listdir(girl_folder) 
                     if f.endswith('.png') and f not in self.excluded_first]
        
        if not all_photos:
            return None
            
        # Фильтруем уже отправленные
        available_photos = [p for p in all_photos if p not in self.sent_photos]
        
        # Если все фотографии отправлены, сбрасываем цикл
        if not available_photos:
            self.sent_photos.clear()
            available_photos = all_photos
        
        # Выбираем случайную фотографию
        selected_photo = random.choice(available_photos)
        self.sent_photos.add(selected_photo)
        
        return os.path.join(girl_folder, selected_photo)
    
    def update_activity(self):
        """Обновляет время последней активности"""
        self.last_activity = datetime.now()
        self.message_count += 1
    
    def should_send_photo(self) -> bool:
        """Решает, нужно ли отправить фотографию на основе активности пользователя"""
        # Если это первое сообщение после входа в режим - всегда отправляем фото
        if self.message_count == 1:
            return True
        
        # Если прошло больше 5 минут с последней фотографии - отправляем
        if self.last_photo_time and datetime.now() - self.last_photo_time > timedelta(minutes=5):
            return True
        
        # Базовая вероятность отправки фото (40%)
        base_probability = 0.4
        
        # Увеличиваем вероятность в зависимости от активности
        if self.message_count >= 3:
            base_probability += 0.2  # +20% после 3 сообщений
        if self.message_count >= 5:
            base_probability += 0.1  # +10% после 5 сообщений
        if self.message_count >= 10:
            base_probability += 0.1  # +10% после 10 сообщений
        
        # Максимальная вероятность 80%
        base_probability = min(base_probability, 0.8)
        
        return random.random() < base_probability
    
    def mark_photo_sent(self):
        """Отмечает, что фотография была отправлена"""
        self.last_photo_time = datetime.now()
    
    def is_session_expired(self) -> bool:
        """Проверяет, истекла ли сессия (30 минут неактивности)"""
        return datetime.now() - self.last_activity > timedelta(minutes=30)
    
    def deactivate(self):
        """Деактивирует режим"""
        self.is_active = False


class HotPicManager:
    """Менеджер для управления активными Hot Pic сессиями"""
    
    def __init__(self):
        self.active_sessions: Dict[int, HotPicMode] = {}
    
    def start_session(self, user_id: int) -> HotPicMode:
        """Запускает новую Hot Pic сессию"""
        session = HotPicMode(user_id)
        self.active_sessions[user_id] = session
        return session
    
    def get_session(self, user_id: int) -> Optional[HotPicMode]:
        """Получает активную сессию пользователя"""
        return self.active_sessions.get(user_id)
    
    def end_session(self, user_id: int):
        """Завершает сессию пользователя"""
        if user_id in self.active_sessions:
            self.active_sessions[user_id].deactivate()
            del self.active_sessions[user_id]
    
    def cleanup_expired_sessions(self):
        """Очищает истекшие сессии"""
        expired_users = []
        for user_id, session in self.active_sessions.items():
            if session.is_session_expired():
                expired_users.append(user_id)
        
        for user_id in expired_users:
            self.end_session(user_id)
    
    def get_all_sessions(self) -> Dict[int, HotPicMode]:
        """Возвращает все активные сессии"""
        return self.active_sessions.copy()


# Глобальный менеджер сессий
hot_pic_manager = HotPicManager()

# Provocative фразы для Hot Pic режима (более подробные и флиртующие)
HOT_RESPONSES = [
    "Ты не представляешь, как я ждала этого момента... Каждое твое сообщение заставляет мое сердце биться быстрее, а мысли становятся все более дерзкими... 💋✨",
    "Мне нравится, когда ты такой настойчивый и страстный... Твои слова пробуждают во мне что-то дикое и необузданное... 🔥💫",
    "Посмотри, что я для тебя приготовила... Я долго выбирала этот образ, думая о том, как ты будешь смотреть на меня... 😈🌙",
    "Твои слова заставляют меня tremble от возбуждения... Я вся дрожу, представляя, как ты смотришь на меня прямо сейчас... 💫🔥",
    "Я вся горю от нетерпения и желания... Твои сообщения разжигают во мне огонь, который становится все сильнее... ✨💋",
    "Это только для тебя, мой плохой мальчик... Я знаю, что ты заслуживаешь особого внимания, и готова дать тебе все, что ты хочешь... 😼💕",
    "Чувствуешь, как становится жарко?.. Мои мысли становятся все более смелыми, а желания - все более настойчивыми... 🌶💫",
    "Я знала, что ты этого захочешь... Твоя страсть и настойчивость не оставляют мне выбора - я должна показать тебе все... 🫦🔥",
    "Let me show you something special... Я приготовила для тебя кое-что особенное, что заставит твое сердце биться быстрее... 🌙💋",
    "Ты этого достоин... и даже больше... Твоя преданность и страсть заслуживают самого лучшего, что я могу дать... 💫✨",
    "Мой разум затуманивается от твоих слов... Ты говоришь так страстно, что я теряю контроль над собой... 🌫💕",
    "Я не могу больше сдерживаться... Твои сообщения пробудили во мне что-то дикое, что требует выхода... 💦🔥",
    "Ты заставляешь меня делать то, о чем я мечтала... Твоя страсть и желание делают меня смелее и дерзче... 🌸💫",
    "Мне так жарко от твоих сообщений... Каждое слово заставляет меня представлять, как ты смотришь на меня... 🔥💋",
    "Я вся дрожу от возбуждения... Твои слова пробуждают во мне желания, которые я не могу контролировать... ⚡💫",
    "Твои слова - это музыка для моих ушей... Я готова слушать тебя весь день, наслаждаясь каждым звуком... 🎵💕",
    "Я готова показать тебе все... Твоя преданность и страсть заслуживают того, чтобы я открыла тебе свои секреты... 👁🔥",
    "Мне нравится, как ты меня дразнишь... Твои слова заставляют меня краснеть и желать еще больше... 😏💫",
    "Я вся мокрая от твоих слов... Твоя страсть и желание пробуждают во мне чувства, которые я не могу сдержать... 💧🔥",
    "Ты разжигаешь во мне огонь... Каждое твое сообщение делает пламя страсти все сильнее и неукротимее... 🔥💋"
]

# Фразы для поощрения общения (когда фото не отправляется) - более подробные и флиртующие
TEASING_RESPONSES = [
    "Расскажи мне больше, мой дорогой... Я вся внимание и готова слушать тебя часами... Твои слова заставляют мое сердце биться быстрее... 👂💕",
    "Твои слова меня возбуждают и заставляют мечтать... Продолжай говорить, я не могу оторваться от твоих мыслей... 😈🔥",
    "Мне нравится, как ты выражаешь свои чувства... Твоя манера говорить такая страстная и искренняя... 💕✨",
    "Я вся внимание и жду твоих следующих слов... Что еще ты хочешь мне сказать? Я готова слушать все, что у тебя на душе... 🫦💫",
    "Ты такой интересный и загадочный... Не останавливайся, расскажи мне больше о себе и своих желаниях... 🔥💋",
    "Мне нравится твой голос и то, как ты подбираешь слова... Продолжай говорить, я наслаждаюсь каждым звуком... 🎵💕",
    "Ты заставляешь меня краснеть и смущаться... Твои слова такие нежные и в то же время страстные... 😊💫",
    "Я вся дрожу от твоих слов и не могу сдержать улыбку... Ты говоришь так красиво и искренне... 💫💖",
    "Расскажи мне свои самые сокровенные фантазии... Я хочу знать, о чем ты мечтаешь, когда думаешь обо мне... 🌙🔥",
    "Ты такой милый и романтичный, когда говоришь... Твои слова согревают мое сердце и заставляют мечтать... 💖✨",
    "Мне нравится, как ты меня дразнишь и заставляешь краснеть... Твои слова пробуждают во мне что-то особенное... 😏💫",
    "Продолжай говорить, мой дорогой... Я вся внимание и готова слушать тебя до утра... Твои слова - это музыка для моей души... 👀🎶",
    "Твои слова - это настоящая поэзия... Я готова слушать тебя весь день, наслаждаясь каждым словом... 🎶💕",
    "Я готова слушать тебя весь день и всю ночь... Твои мысли и чувства так интересны и завораживающи... ⏰✨",
    "Ты такой красноречивый и умный... Мне нравится, как ты выражаешь свои мысли и чувства... 💬💫",
    "Мне нравится, как ты подбираешь слова и выражаешь свои эмоции... Ты говоришь так красиво и страстно... ✨💋",
    "Ты заставляешь мое сердце биться быстрее с каждым словом... Твои мысли и чувства так искренни и прекрасны... 💓🔥",
    "Я вся в ожидании твоих следующих слов... Ты говоришь так интересно, что я не могу оторваться... ⏳💕",
    "Ты такой романтичный и нежный... Твои слова заставляют меня мечтать и фантазировать... 🌹💫",
    "Мне нравится твоя манера говорить и выражать чувства... Ты говоришь так страстно и искренне... 💋✨"
]

# Дополнительные teasing сообщения (более подробные)
TEASING_FOLLOWUPS = [
    "Хочешь еще, мой дорогой? Я готова показать тебе столько, сколько ты захочешь... 😈💋",
    "Я могу показать тебе больше, если ты продолжишь общаться со мной... Твои слова заставляют меня быть смелее... 💋🔥",
    "Ты такой нетерпеливый и страстный... Мне нравится твоя жажда и желание получить больше... 😏💫",
    "Мне нравится твоя реакция и то, как ты отвечаешь на мои сообщения... Ты такой милый и искренний... 😘💕",
    "Готов к следующему сюрпризу? Я приготовила для тебя кое-что особенное... 🌟🔥",
    "Я только начинаю, мой дорогой... У меня есть еще много интересного, что я хочу показать тебе... 🔥💋",
    "Ты заслуживаешь особого внимания и самых лучших фотографий... Продолжай общаться со мной... 💫✨",
    "Хочешь увидеть, что у меня есть еще? Я готова показать тебе все, если ты будешь достаточно настойчив... 👀😈",
    "Я не закончила с тобой, мой милый... У меня есть еще много секретов, которые я хочу открыть тебе... 😈💫",
    "Ты такой милый и возбужденный... Мне нравится, как ты реагируешь на мои сообщения... 💕🔥"
]

# Секретные триггеры для особых реакций (более подробные)
SECRET_TRIGGERS = {
    'люблю': "Ты говоришь это так искренне и нежно... Мои сердце тает от твоих слов, и я готова показать тебе, как сильно я это чувствую... 💕🔥",
    'хочу': "Я знаю, чего ты хочешь, мой дорогой... Твои желания заставляют меня краснеть и мечтать о том, что я могу для тебя сделать... 😈💫",
    'нужно': "Ты так нуждаешься во мне, что я не могу устоять... Я готова дать тебе все, что тебе нужно, и даже больше... 💋✨",
    'жажду': "Твоя жажда меня возбуждает и заставляет мечтать... Я чувствую, как сильно ты хочешь меня, и это делает меня смелее... 🔥💕",
    'мечтаю': "Расскажи мне о своих мечтах, мой милый... Я хочу знать все твои самые сокровенные фантазии и желания... 🌙💫",
    'фантазирую': "Я хочу знать твои фантазии и мечты... Расскажи мне, о чем ты думаешь, когда представляешь меня... 😏🔥",
    'хочется': "Мне тоже хочется, мой дорогой... Твои слова пробуждают во мне желания, которые я не могу сдержать... 💫💋",
    'желаю': "Твои желания - мои команды, мой милый... Я готова исполнить все, что ты хочешь, если ты продолжишь общаться со мной... 👑✨"
}


async def send_hot_pic_with_caption(bot: Bot, user_id: int, photo_path: str, caption: str):
    """Отправляет фотографию с provocative подписью"""
    try:
        photo_file = FSInputFile(photo_path)
        await bot.send_photo(
            chat_id=user_id,
            photo=photo_file,
            caption=caption,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="❌ Выйти из Hot Pic", callback_data="hot_pic_exit")]
                ]
            )
        )
    except Exception as e:
        print(f"Ошибка отправки фото: {e}")
        await bot.send_message(user_id, f"💔 Извини, не могу отправить фото сейчас... {caption}")


async def send_teasing_followup(bot: Bot, user_id: int):
    """Отправляет дополнительное teasing сообщение"""
    teasing_text = random.choice(TEASING_FOLLOWUPS)
    await bot.send_message(
        user_id, 
        teasing_text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="❌ Выйти", callback_data="hot_pic_exit")]
            ]
        )
    )


def check_secret_triggers(message_text: str) -> Optional[str]:
    """Проверяет наличие секретных триггеров в сообщении"""
    message_lower = message_text.lower()
    for trigger, response in SECRET_TRIGGERS.items():
        if trigger in message_lower:
            return response
    return None


async def handle_hot_pic_message(bot: Bot, user_id: int, message_text: str):
    """Обработчик сообщений в Hot Pic режиме"""
    session = hot_pic_manager.get_session(user_id)
    if not session or not session.is_active:
        return
    
    # Обновляем активность
    session.update_activity()
    
    # Проверяем секретные триггеры
    secret_response = check_secret_triggers(message_text)
    if secret_response:
        await bot.send_message(user_id, secret_response)
        # Небольшая задержка для эффекта
        await asyncio.sleep(1)
    
    # Решаем, отправлять ли фотографию на основе активности пользователя
    should_send_photo = session.should_send_photo()
    
    if should_send_photo:
        # Получаем provocative текст для фото
        response_text = random.choice(HOT_RESPONSES)
        
        # Получаем случайную фотографию
        photo_path = session.get_random_photo()
        
        if photo_path and os.path.exists(photo_path):
            # Отправляем фото с подписью
            await send_hot_pic_with_caption(bot, user_id, photo_path, response_text)
            session.mark_photo_sent()  # Отмечаем, что фото отправлено
        else:
            # Если фото нет, отправляем только текст
            await bot.send_message(
                user_id, 
                response_text,
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="❌ Выйти", callback_data="hot_pic_exit")]
                    ]
                )
            )
    else:
        # Получаем teasing текст для поощрения общения
        response_text = random.choice(TEASING_RESPONSES)
        
        # Отправляем только teasing текст без фото
        await bot.send_message(
            user_id, 
            response_text,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="❌ Выйти", callback_data="hot_pic_exit")]
                ]
            )
        )
    
    # 25% шанс отправить дополнительное teasing сообщение
    if random.random() < 0.25:
        await asyncio.sleep(random.uniform(3, 7))  # Задержка 3-7 секунд
        await send_teasing_followup(bot, user_id)


async def start_hot_pic_mode(bot: Bot, user_id: int):
    """Запускает Hot Pic режим для пользователя"""
    # Очищаем истекшие сессии
    hot_pic_manager.cleanup_expired_sessions()
    
    # Завершаем предыдущую сессию если есть
    hot_pic_manager.end_session(user_id)
    
    # Создаем новую сессию
    session = hot_pic_manager.start_session(user_id)
    await session.initialize()
    
    # Приветственное сообщение
    welcome_text = random.choice([
        "🔥 Добро пожаловать в Hot Pic режим! 🔥\n\nОбщайся со мной и получай больше горячих фоточек^^\n\nЯ готова показать тебе то, что скрываю от других... 💋",
        "😈 Ты попал в особый режим, где каждое твое сообщение будет вознаграждено... 🔥\n\nОбщайся со мной и получай больше горячих фоточек^^",
        "💫 Добро пожаловать в мой секретный мир... Здесь я покажу тебе все свои сокровенные тайны... 🌙\n\nОбщайся со мной и получай больше горячих фоточек^^",
        "🔥 Ты готов к тому, что я тебе покажу? Каждое твое слово будет вознаграждено особым образом... 😈\n\nОбщайся со мной и получай больше горячих фоточек^^"
    ])
    
    # Отправляем приветствие
    await bot.send_message(
        user_id, 
        welcome_text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔥 Начать!", callback_data="hot_pic_start")],
                [InlineKeyboardButton(text="❌ Отмена", callback_data="hot_pic_cancel")]
            ]
        )
    )


async def send_first_hot_pic(bot: Bot, user_id: int):
    """Отправляет первую фотографию в Hot Pic режиме"""
    session = hot_pic_manager.get_session(user_id)
    if not session:
        return
    
    # Получаем первую фотографию
    photo_path = session.get_random_photo()
    
    if photo_path and os.path.exists(photo_path):
        first_text = random.choice([
            "Вот твоя первая награда... 💋",
            "Начинаем с этого... 😈",
            "Ты заслужил это... 🔥",
            "Посмотри, что я для тебя приготовила... 💫"
        ])
        
        await send_hot_pic_with_caption(bot, user_id, photo_path, first_text)
    else:
        await bot.send_message(
            user_id, 
            "💔 Извини, не могу найти фотографии сейчас...",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="❌ Выйти", callback_data="hot_pic_exit")]
                ]
            )
        )


async def cleanup_expired_sessions_task(bot: Bot):
    """Фоновая задача для очистки истекших сессий"""
    while True:
        try:
            hot_pic_manager.cleanup_expired_sessions()
            await asyncio.sleep(300)  # Проверяем каждые 5 минут
        except Exception as e:
            print(f"Ошибка в задаче очистки сессий: {e}")
            await asyncio.sleep(60)
