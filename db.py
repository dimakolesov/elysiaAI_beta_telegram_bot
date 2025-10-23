from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Optional, List, Tuple, Dict

import aiosqlite

DB_PATH: str = os.getenv("DB_PATH", "./data.sqlite3")


async def init_db() -> None:
    """Инициализация таблиц БД."""
    async with aiosqlite.connect(DB_PATH) as db:
        # users: базовая информация о пользователях
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                user_name TEXT,
                gender TEXT CHECK(gender IN ('male','female')),
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                points INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                last_message_date DATE,
                streak_days INTEGER DEFAULT 0,
                trial_status TEXT DEFAULT NULL,
                trial_activated_at TIMESTAMP DEFAULT NULL
            );
            """
        )
        
        # access: подписка и доступ
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS access (
                user_id INTEGER PRIMARY KEY,
                expires_at TIMESTAMP,
                type TEXT CHECK(type IN ('trial','paid')) NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            );
            """
        )
        
        # prefs: предпочтения пользователя
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS prefs (
                user_id INTEGER PRIMARY KEY,
                girl TEXT DEFAULT 'Подруга',
                mood TEXT DEFAULT 'happy',
                relationship_level INTEGER DEFAULT 1,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            );
            """
        )
        
        # personalization: настройки персонализации Элизии
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS personalization (
                user_id INTEGER PRIMARY KEY,
                personality_type TEXT DEFAULT 'sweet',
                communication_style TEXT DEFAULT 'casual',
                custom_traits TEXT DEFAULT '',
                custom_phrases TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            );
            """
        )
        
        # memory: история сообщений
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                role TEXT CHECK(role IN ('user','assistant','system')) NOT NULL,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            );
            """
        )
        
        # stats: очки симпатии и статистика
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS stats (
                user_id INTEGER PRIMARY KEY,
                hearts INTEGER DEFAULT 0,
                total_messages INTEGER DEFAULT 0,
                days_active INTEGER DEFAULT 0,
                last_heart_date DATE,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            );
            """
        )
        
        # achievements: достижения пользователя
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                achievement_type TEXT NOT NULL,
                unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            );
            """
        )
        
        
        # unlocked_rewards: разблокированные награды за очки
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS unlocked_rewards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                reward_type TEXT NOT NULL,
                reward_name TEXT NOT NULL,
                unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            );
            """
        )
        
        # bans: блокировки
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS bans (
                user_id INTEGER PRIMARY KEY,
                reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            );
            """
        )
        
        # referrals: реферальная система
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER NOT NULL,
                referred_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                subscription_activated BOOLEAN DEFAULT FALSE,
                commission_earned REAL DEFAULT 0.0,
                FOREIGN KEY(referrer_id) REFERENCES users(user_id),
                FOREIGN KEY(referred_id) REFERENCES users(user_id),
                UNIQUE(referred_id)
            );
            """
        )
        
        # referral_stats: статистика рефералов
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS referral_stats (
                user_id INTEGER PRIMARY KEY,
                total_referrals INTEGER DEFAULT 0,
                active_referrals INTEGER DEFAULT 0,
                total_earnings REAL DEFAULT 0.0,
                last_commission_at TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            );
            """
        )
        
        await db.commit()


async def upsert_user(user_id: int, username: Optional[str] = None) -> None:
    """Создать или обновить пользователя."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO users(user_id, username)
            VALUES(?, ?)
            ON CONFLICT(user_id) DO UPDATE SET 
                username=excluded.username
            """,
            (user_id, username),
        )
        await db.commit()


async def set_user_name(user_id: int, name: str) -> None:
    """Установить имя пользователя."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET user_name=? WHERE user_id=?", (name, user_id))
        await db.commit()


async def get_user_name(user_id: int) -> Optional[str]:
    """Получить имя пользователя."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_name FROM users WHERE user_id=?", (user_id,)) as cur:
            row = await cur.fetchone()
            return row[0] if row and row[0] else None


async def set_gender(user_id: int, gender: str) -> None:
    """Установить пол пользователя."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET gender=? WHERE user_id=?", (gender, user_id))
        await db.commit()


async def get_gender(user_id: int) -> Optional[str]:
    """Получить пол пользователя."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT gender FROM users WHERE user_id=?", (user_id,)) as cur:
            row = await cur.fetchone()
            return row[0] if row and row[0] else None


async def grant_access(user_id: int, days: int, access_type: str = "trial") -> None:
    """Предоставить доступ пользователю."""
    now = datetime.utcnow()
    expires = now + timedelta(days=days)
    expires_str = expires.strftime("%Y-%m-%d %H:%M:%S")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO access(user_id, expires_at, type)
            VALUES(?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET expires_at=excluded.expires_at, type=excluded.type
            """,
            (user_id, expires_str, access_type),
        )
        await db.commit()


async def has_access(user_id: int) -> bool:
    """Проверить, есть ли у пользователя доступ."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT expires_at FROM access WHERE user_id = ?", (user_id,)
        ) as cur:
            row = await cur.fetchone()
            if not row or not row[0]:
                return False
            try:
                expires = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return False
            return expires > datetime.utcnow()


async def get_access_type(user_id: int) -> Optional[str]:
    """Получить тип доступа пользователя."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT type FROM access WHERE user_id=?", (user_id,)) as cur:
            row = await cur.fetchone()
            return row[0] if row and row[0] else None


async def set_girl(user_id: int, girl: str) -> None:
    """Установить выбранную девушку."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO prefs(user_id, girl)
            VALUES(?, ?)
            ON CONFLICT(user_id) DO UPDATE SET girl=excluded.girl
            """,
            (user_id, girl),
        )
        await db.commit()


async def get_girl(user_id: int) -> Optional[str]:
    """Получить выбранную девушку."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT girl FROM prefs WHERE user_id = ?", (user_id,)
        ) as cur:
            row = await cur.fetchone()
            return row[0] if row and row[0] else "Подруга"


async def set_mood(user_id: int, mood: str) -> None:
    """Установить настроение девушки."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO prefs(user_id, mood)
            VALUES(?, ?)
            ON CONFLICT(user_id) DO UPDATE SET mood=excluded.mood
            """,
            (user_id, mood),
        )
        await db.commit()


async def get_mood(user_id: int) -> str:
    """Получить настроение девушки."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT mood FROM prefs WHERE user_id = ?", (user_id,)
        ) as cur:
            row = await cur.fetchone()
            return row[0] if row and row[0] else "happy"


async def set_relationship_level(user_id: int, level: int) -> None:
    """Установить уровень отношений."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO prefs(user_id, relationship_level)
            VALUES(?, ?)
            ON CONFLICT(user_id) DO UPDATE SET relationship_level=excluded.relationship_level
            """,
            (user_id, level),
        )
        await db.commit()


async def get_relationship_level(user_id: int) -> int:
    """Получить уровень отношений."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT relationship_level FROM prefs WHERE user_id = ?", (user_id,)
        ) as cur:
            row = await cur.fetchone()
            return row[0] if row and row[0] else 1


async def save_message(user_id: int, message: str, role: str) -> None:
    """Сохранить сообщение в память."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO memory(user_id, message, role) VALUES(?, ?, ?)",
            (user_id, message, role),
        )
        await db.commit()


async def get_memory(user_id: int, limit: int = 20) -> List[Tuple[str, str]]:
    """Получить историю сообщений."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT message, role FROM memory WHERE user_id=? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        ) as cur:
            rows = await cur.fetchall()
            return [(r[0], r[1]) for r in rows][::-1]


async def add_hearts(user_id: int, amount: int = 1) -> None:
    """Добавить очки симпатии."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO stats(user_id, hearts, total_messages, last_heart_date) VALUES(?, ?, 1, CURRENT_DATE) "
            "ON CONFLICT(user_id) DO UPDATE SET hearts=stats.hearts+?, total_messages=stats.total_messages+1, last_heart_date=CURRENT_DATE",
            (user_id, amount, amount),
        )
        await db.commit()


async def get_hearts(user_id: int) -> int:
    """Получить количество очков симпатии."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT hearts FROM stats WHERE user_id=?", (user_id,)) as cur:
            row = await cur.fetchone()
            return int(row[0]) if row and row[0] is not None else 0


async def get_total_messages(user_id: int) -> int:
    """Получить общее количество сообщений."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT total_messages FROM stats WHERE user_id=?", (user_id,)) as cur:
            row = await cur.fetchone()
            return int(row[0]) if row and row[0] is not None else 0


async def add_achievement(user_id: int, achievement_type: str) -> None:
    """Добавить достижение пользователю."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Проверяем, есть ли уже такое достижение
        async with db.execute(
            "SELECT 1 FROM achievements WHERE user_id=? AND achievement_type=?", 
            (user_id, achievement_type)
        ) as cur:
            if await cur.fetchone():
                return  # Достижение уже есть
        
        await db.execute(
            "INSERT INTO achievements(user_id, achievement_type) VALUES(?, ?)",
            (user_id, achievement_type),
        )
        await db.commit()


async def get_achievements(user_id: int) -> List[str]:
    """Получить достижения пользователя."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT achievement_type FROM achievements WHERE user_id=? ORDER BY unlocked_at DESC",
            (user_id,)
        ) as cur:
            rows = await cur.fetchall()
            return [row[0] for row in rows]




async def set_ban(user_id: int, reason: str | None = None) -> None:
    """Забанить пользователя."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO bans(user_id, reason) VALUES(?, ?)", (user_id, reason)
        )
        await db.commit()


async def unset_ban(user_id: int) -> None:
    """Разбанить пользователя."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM bans WHERE user_id=?", (user_id,))
        await db.commit()

async def ban_user(user_id: int, reason: str = "Нарушение правил") -> None:
    """Забанить пользователя."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO bans (user_id, reason, banned_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
            (user_id, reason)
        )
        await db.commit()


async def is_banned(user_id: int) -> bool:
    """Проверить, забанен ли пользователь."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT 1 FROM bans WHERE user_id=?", (user_id,)) as cur:
            row = await cur.fetchone()
            return bool(row)

async def get_user_trial_status(user_id: int) -> Optional[str]:
    """Получает статус пробного дня пользователя."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT trial_status FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row and row[0] else None

async def set_user_trial_status(user_id: int, status: str) -> None:
    """Устанавливает статус пробного дня пользователя."""
    async with aiosqlite.connect(DB_PATH) as db:
        if status == "active":
            await db.execute(
                "UPDATE users SET trial_status = ?, trial_activated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                (status, user_id)
            )
        else:
            await db.execute(
                "UPDATE users SET trial_status = ? WHERE user_id = ?",
                (status, user_id)
            )
        await db.commit()


# ==================== СИСТЕМА ОЧКОВ БЛИЗОСТИ ====================

async def add_points(user_id: int, amount: int) -> None:
    """Добавляет очки пользователю."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET points = points + ? WHERE user_id = ?", 
            (amount, user_id)
        )
        await db.commit()


async def get_points(user_id: int) -> int:
    """Возвращает текущее количество очков."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT points FROM users WHERE user_id = ?", 
            (user_id,)
        ) as cur:
            row = await cur.fetchone()
            return row[0] if row else 0


async def get_level(user_id: int) -> int:
    """Возвращает текущий уровень близости."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT level FROM users WHERE user_id = ?", 
            (user_id,)
        ) as cur:
            row = await cur.fetchone()
            return row[0] if row else 1


async def level_up(user_id: int) -> None:
    """Повышает уровень при достижении порога."""
    points = await get_points(user_id)
    current_level = await get_level(user_id)
    
    # Пороги для повышения уровня (1-10)
    level_thresholds = [0, 100, 250, 500, 800, 1200, 1700, 2300, 3000, 4000]
    
    new_level = current_level
    for i, threshold in enumerate(level_thresholds[1:], 1):
        if points >= threshold and i > current_level:
            new_level = i
    
    if new_level > current_level:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "UPDATE users SET level = ? WHERE user_id = ?", 
                (new_level, user_id)
            )
            await db.commit()


async def get_streak_days(user_id: int) -> int:
    """Возвращает количество дней подряд общения."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT streak_days FROM users WHERE user_id = ?", 
            (user_id,)
        ) as cur:
            row = await cur.fetchone()
            return row[0] if row else 0


async def update_streak(user_id: int) -> int:
    """Обновляет streak пользователя и возвращает бонусные очки."""
    from datetime import date, timedelta
    
    today = date.today()
    async with aiosqlite.connect(DB_PATH) as db:
        # Получаем последнюю дату сообщения
        async with db.execute(
            "SELECT last_message_date, streak_days FROM users WHERE user_id = ?", 
            (user_id,)
        ) as cur:
            row = await cur.fetchone()
            last_date = row[0] if row and row[0] else None
            current_streak = row[1] if row else 0
        
        bonus_points = 0
        
        if last_date:
            last_date_obj = datetime.strptime(last_date, '%Y-%m-%d').date()
            if last_date_obj == today:
                # Уже писал сегодня, streak не обновляем
                return 0
            elif last_date_obj == today - timedelta(days=1):
                # Писал вчера, продолжаем streak
                new_streak = current_streak + 1
            else:
                # Пропустил день, сбрасываем streak
                new_streak = 1
        else:
            # Первое сообщение
            new_streak = 1
        
        # Обновляем streak и дату
        await db.execute(
            "UPDATE users SET streak_days = ?, last_message_date = ? WHERE user_id = ?", 
            (new_streak, today, user_id)
        )
        
        # Проверяем бонусы за streak
        if new_streak == 3:
            bonus_points = 20
        elif new_streak == 5:
            bonus_points = 50
        elif new_streak == 7:
            bonus_points = 100
        elif new_streak > 7 and new_streak % 7 == 0:
            bonus_points = 50  # Каждые 7 дней дополнительный бонус
        
        await db.commit()
        return bonus_points


async def unlock_reward(user_id: int, reward_type: str, reward_name: str) -> bool:
    """Разблокирует награду для пользователя."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Проверяем, не разблокирована ли уже
        async with db.execute(
            "SELECT 1 FROM unlocked_rewards WHERE user_id = ? AND reward_type = ? AND reward_name = ?", 
            (user_id, reward_type, reward_name)
        ) as cur:
            if await cur.fetchone():
                return False  # Уже разблокирована
        
        # Разблокируем
        await db.execute(
            "INSERT INTO unlocked_rewards(user_id, reward_type, reward_name) VALUES(?, ?, ?)", 
            (user_id, reward_type, reward_name)
        )
        await db.commit()
        return True


async def get_unlocked_rewards(user_id: int) -> List[Tuple[str, str]]:
    """Возвращает список разблокированных наград."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT reward_type, reward_name FROM unlocked_rewards WHERE user_id = ? ORDER BY unlocked_at", 
            (user_id,)
        ) as cur:
            return await cur.fetchall()


async def get_level_progress(user_id: int) -> Tuple[int, int, int]:
    """Возвращает (текущий_уровень, текущие_очки, очки_до_следующего_уровня)."""
    points = await get_points(user_id)
    current_level = await get_level(user_id)
    
    level_thresholds = [0, 100, 250, 500, 800, 1200, 1700, 2300, 3000, 4000]
    
    if current_level >= 10:
        return current_level, points, 0  # Максимальный уровень
    
    current_threshold = level_thresholds[current_level - 1]
    next_threshold = level_thresholds[current_level]
    progress = points - current_threshold
    needed = next_threshold - current_threshold
    
    return current_level, progress, needed


async def get_all_user_ids() -> List[int]:
    """Получить всех пользователей."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM users") as cur:
            rows = await cur.fetchall()
            return [int(r[0]) for r in rows]


async def get_days_active(user_id: int) -> int:
    """Получить количество дней активности пользователя."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT days_active FROM stats WHERE user_id=?", (user_id,)) as cur:
            row = await cur.fetchone()
            return int(row[0]) if row and row[0] is not None else 0


async def update_days_active(user_id: int) -> None:
    """Обновить количество дней активности пользователя."""
    from datetime import date
    
    today = date.today()
    async with aiosqlite.connect(DB_PATH) as db:
        # Получаем последнюю дату активности
        async with db.execute(
            "SELECT last_heart_date FROM stats WHERE user_id = ?", 
            (user_id,)
        ) as cur:
            row = await cur.fetchone()
            last_active_date = row[0] if row and row[0] else None
        
        if last_active_date:
            last_date_obj = datetime.strptime(last_active_date, '%Y-%m-%d').date()
            if last_date_obj != today:
                # Новый день активности
                await db.execute(
                    "UPDATE stats SET days_active = days_active + 1, last_heart_date = ? WHERE user_id = ?", 
                    (today, user_id)
                )
                await db.commit()
        else:
            # Первый день активности
            await db.execute(
                "INSERT INTO stats(user_id, days_active, last_heart_date) VALUES(?, 1, ?) ON CONFLICT(user_id) DO UPDATE SET days_active = days_active + 1, last_heart_date = ?", 
                (user_id, today, today)
            )
            await db.commit()


async def get_stats() -> Dict:
    """Получить общую статистику."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*), SUM(hearts), SUM(total_messages) FROM stats") as cur:
            row = await cur.fetchone()
            return {
                "users": row[0] or 0, 
                "hearts": row[1] or 0,
                "messages": row[2] or 0
            }

async def save_user_fact(user_id: int, fact_type: str, fact_content: str, confidence: float) -> None:
    """Сохранить факт о пользователе"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS user_facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                fact_type TEXT,
                fact_content TEXT,
                confidence REAL,
                first_mentioned DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_mentioned DATETIME DEFAULT CURRENT_TIMESTAMP,
                mention_count INTEGER DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Проверяем, существует ли уже такой факт
        async with db.execute('''
            SELECT id, mention_count FROM user_facts 
            WHERE user_id = ? AND fact_type = ? AND fact_content = ?
        ''', (user_id, fact_type, fact_content)) as cursor:
            existing = await cursor.fetchone()
        
        if existing:
            # Обновляем существующий факт
            await db.execute('''
                UPDATE user_facts 
                SET mention_count = mention_count + 1,
                    last_mentioned = CURRENT_TIMESTAMP,
                    confidence = MAX(confidence, ?)
                WHERE id = ?
            ''', (confidence, existing[0]))
        else:
            # Создаем новый факт
            await db.execute('''
                INSERT INTO user_facts (user_id, fact_type, fact_content, confidence)
                VALUES (?, ?, ?, ?)
            ''', (user_id, fact_type, fact_content, confidence))
        
        await db.commit()

async def get_user_facts(user_id: int, fact_type: str = None) -> List[Tuple]:
    """Получить факты о пользователе"""
    async with aiosqlite.connect(DB_PATH) as db:
        if fact_type:
            async with db.execute('''
                SELECT fact_type, fact_content, confidence, first_mentioned, last_mentioned, mention_count
                FROM user_facts 
                WHERE user_id = ? AND fact_type = ?
                ORDER BY mention_count DESC, confidence DESC
            ''', (user_id, fact_type)) as cursor:
                return await cursor.fetchall()
        else:
            async with db.execute('''
                SELECT fact_type, fact_content, confidence, first_mentioned, last_mentioned, mention_count
                FROM user_facts 
                WHERE user_id = ?
                ORDER BY mention_count DESC, confidence DESC
            ''', (user_id,)) as cursor:
                return await cursor.fetchall()

async def save_conversation_topic(user_id: int, topic: str, sentiment: str) -> None:
    """Сохранить тему разговора"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS conversation_topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                topic TEXT,
                first_discussed DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_discussed DATETIME DEFAULT CURRENT_TIMESTAMP,
                discussion_count INTEGER DEFAULT 1,
                sentiment TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Проверяем, существует ли уже такая тема
        async with db.execute('''
            SELECT id, discussion_count FROM conversation_topics 
            WHERE user_id = ? AND topic = ?
        ''', (user_id, topic)) as cursor:
            existing = await cursor.fetchone()
        
        if existing:
            # Обновляем существующую тему
            await db.execute('''
                UPDATE conversation_topics 
                SET discussion_count = discussion_count + 1,
                    last_discussed = CURRENT_TIMESTAMP,
                    sentiment = ?
                WHERE id = ?
            ''', (sentiment, existing[0]))
        else:
            # Создаем новую тему
            await db.execute('''
                INSERT INTO conversation_topics (user_id, topic, sentiment)
                VALUES (?, ?, ?)
            ''', (user_id, topic, sentiment))
        
        await db.commit()

async def get_conversation_topics(user_id: int, limit: int = 10) -> List[Tuple]:
    """Получить темы разговоров пользователя"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('''
            SELECT topic, first_discussed, last_discussed, discussion_count, sentiment
            FROM conversation_topics 
            WHERE user_id = ?
            ORDER BY last_discussed DESC
            LIMIT ?
        ''', (user_id, limit)) as cursor:
            return await cursor.fetchall()


# ==================== ФУНКЦИИ ПЕРСОНАЛИЗАЦИИ ====================

async def save_personalization_settings(user_id: int, personality_type: str, communication_style: str, 
                                      custom_traits: List[str] = None, custom_phrases: List[str] = None) -> None:
    """Сохранить настройки персонализации пользователя"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Преобразуем списки в строки для хранения
        traits_str = '\n'.join(custom_traits) if custom_traits else ''
        phrases_str = '\n'.join(custom_phrases) if custom_phrases else ''
        
        await db.execute('''
            INSERT OR REPLACE INTO personalization 
            (user_id, personality_type, communication_style, custom_traits, custom_phrases, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (user_id, personality_type, communication_style, traits_str, phrases_str))
        
        await db.commit()

async def get_personalization_settings(user_id: int) -> Optional[Dict]:
    """Получить настройки персонализации пользователя"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('''
            SELECT personality_type, communication_style, custom_traits, custom_phrases, created_at, updated_at
            FROM personalization 
            WHERE user_id = ?
        ''', (user_id,)) as cursor:
            result = await cursor.fetchone()
            
            if not result:
                return None
            
            # Преобразуем строки обратно в списки
            custom_traits = [t.strip() for t in result[2].split('\n') if t.strip()] if result[2] else []
            custom_phrases = [p.strip() for p in result[3].split('\n') if p.strip()] if result[3] else []
            
            return {
                'personality_type': result[0],
                'communication_style': result[1],
                'custom_traits': custom_traits,
                'custom_phrases': custom_phrases,
                'created_at': result[4],
                'updated_at': result[5]
            }

async def has_personalization_settings(user_id: int) -> bool:
    """Проверить, есть ли у пользователя настройки персонализации"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('''
            SELECT 1 FROM personalization WHERE user_id = ?
        ''', (user_id,)) as cursor:
            result = await cursor.fetchone()
            return result is not None

async def delete_personalization_settings(user_id: int) -> None:
    """Удалить настройки персонализации пользователя"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            DELETE FROM personalization WHERE user_id = ?
        ''', (user_id,))
        await db.commit()


# ==================== ФУНКЦИИ РЕФЕРАЛЬНОЙ СИСТЕМЫ ====================

async def create_referral_link(user_id: int) -> str:
    """Создать реферальную ссылку для пользователя"""
    return f"https://t.me/elysia_ai_bot?start={user_id}"

async def process_referral(referred_id: int, referrer_id: int) -> bool:
    """Обработать реферальную регистрацию"""
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            # Проверяем, что пользователь еще не имеет реферера
            async with db.execute('''
                SELECT 1 FROM referrals WHERE referred_id = ?
            ''', (referred_id,)) as cursor:
                if await cursor.fetchone():
                    return False  # У пользователя уже есть реферер
            
            # Создаем запись о реферале
            await db.execute('''
                INSERT INTO referrals (referrer_id, referred_id)
                VALUES (?, ?)
            ''', (referrer_id, referred_id))
            
            # Обновляем статистику реферера
            await db.execute('''
                INSERT OR REPLACE INTO referral_stats 
                (user_id, total_referrals, active_referrals, total_earnings)
                VALUES (?, 
                    COALESCE((SELECT total_referrals FROM referral_stats WHERE user_id = ?), 0) + 1,
                    COALESCE((SELECT active_referrals FROM referral_stats WHERE user_id = ?), 0) + 1,
                    COALESCE((SELECT total_earnings FROM referral_stats WHERE user_id = ?), 0)
                )
            ''', (referrer_id, referrer_id, referrer_id, referrer_id))
            
            await db.commit()
            return True
        except Exception:
            return False

async def get_referral_stats(user_id: int) -> Dict:
    """Получить статистику рефералов пользователя"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('''
            SELECT total_referrals, active_referrals, total_earnings, last_commission_at
            FROM referral_stats WHERE user_id = ?
        ''', (user_id,)) as cursor:
            result = await cursor.fetchone()
            
            if not result:
                return {
                    'total_referrals': 0,
                    'active_referrals': 0,
                    'total_earnings': 0.0,
                    'last_commission_at': None
                }
            
            return {
                'total_referrals': result[0],
                'active_referrals': result[1],
                'total_earnings': result[2],
                'last_commission_at': result[3]
            }

async def get_referral_link(user_id: int) -> str:
    """Получить реферальную ссылку пользователя"""
    return await create_referral_link(user_id)

async def process_subscription_referral(user_id: int) -> Optional[int]:
    """Обработать активацию подписки рефералом и вернуть ID реферера"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Находим реферера
        async with db.execute('''
            SELECT referrer_id FROM referrals 
            WHERE referred_id = ? AND subscription_activated = FALSE
        ''', (user_id,)) as cursor:
            result = await cursor.fetchone()
            
            if not result:
                return None
            
            referrer_id = result[0]
            
            # Отмечаем подписку как активированную
            await db.execute('''
                UPDATE referrals 
                SET subscription_activated = TRUE
                WHERE referred_id = ?
            ''', (user_id,))
            
            # Вычисляем комиссию (50% от стоимости подписки)
            subscription_price = 169.0  # Стоимость подписки
            commission = subscription_price * 0.5
            
            # Обновляем комиссию
            await db.execute('''
                UPDATE referrals 
                SET commission_earned = ?
                WHERE referred_id = ? AND referred_id = ?
            ''', (commission, referrer_id, user_id))
            
            # Обновляем общую статистику реферера
            await db.execute('''
                UPDATE referral_stats 
                SET total_earnings = total_earnings + ?,
                    last_commission_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (commission, referrer_id))
            
            await db.commit()
            return referrer_id

async def get_referral_leaderboard(limit: int = 10) -> List[Tuple[int, str, int, float]]:
    """Получить топ рефереров"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('''
            SELECT rs.user_id, u.username, rs.total_referrals, rs.total_earnings
            FROM referral_stats rs
            JOIN users u ON rs.user_id = u.user_id
            ORDER BY rs.total_earnings DESC
            LIMIT ?
        ''', (limit,)) as cursor:
            return await cursor.fetchall()

async def has_referrer(user_id: int) -> bool:
    """Проверить, есть ли у пользователя реферер"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('''
            SELECT 1 FROM referrals WHERE referred_id = ?
        ''', (user_id,)) as cursor:
            result = await cursor.fetchone()
            return result is not None