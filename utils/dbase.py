from contextlib import asynccontextmanager
import asyncpg
import asyncio
from config import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME
from datetime import datetime

# Глобальная переменная для пула подключений
_user_pool = None


async def init_db():
    """Инициализация пула подключений и создание таблиц"""
    global _user_pool
    if _user_pool is None:
        _user_pool = await asyncpg.create_pool(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT,
            min_size=5,
            max_size=20,
            ssl=False,
        )

        async with _user_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    goal TEXT,
                    days INTEGER DEFAULT 0,
                    everyday INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS steps (
                    step_id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    step TEXT NOT NULL,
                    done INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
                );
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS pomodoro_sessions (
                    session_id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    event_id BIGINT NOT NULL,
                    work_duration INTEGER DEFAULT 1500,
                    break_duration INTEGER DEFAULT 300,
                    long_break_duration INTEGER DEFAULT 900,
                    pomodoros_completed INTEGER DEFAULT 0,
                    is_working BOOLEAN DEFAULT FALSE,
                    is_break BOOLEAN DEFAULT FALSE,
                    time_remaining INTEGER DEFAULT 0,
                    end_time TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
                );
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS pomodoro_stats (
                    stat_id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    event_id BIGINT NOT NULL,
                    pomodoros_completed INTEGER DEFAULT 0,
                    total_work_time INTEGER DEFAULT 0,
                    last_session TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
                    UNIQUE(user_id, event_id)
                );
            """)


            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_pomodoro_user_id 
                ON pomodoro_sessions(user_id);

                CREATE INDEX IF NOT EXISTS idx_pomodoro_event_id 
                ON pomodoro_sessions(event_id);

                CREATE INDEX IF NOT EXISTS idx_pomodoro_active 
                ON pomodoro_sessions(user_id, is_working, is_break);

                CREATE INDEX IF NOT EXISTS idx_pomodoro_stats_user 
                ON pomodoro_stats(user_id);
            """)


@asynccontextmanager
async def get_connection():
    """Асинхронный контекстный менеджер для подключений к БД"""
    if _user_pool is None:
        await init_db()
    async with _user_pool.acquire() as conn:
        yield conn


class Dbase:
    @staticmethod
    async def get_user(user_id):
        """Получить пользователя по ID"""
        async with get_connection() as conn:
            return await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)

    @staticmethod
    async def new_steps(user_id, steps):
        async with get_connection() as conn:
            await conn.execute("""DELETE FROM steps WHERE user_id = $1""", user_id)
            for step in steps:
                print(step)
                await conn.execute("""
                    INSERT INTO steps (user_id, step) VALUES($1, $2)
                """, user_id, step)

    @staticmethod
    async def new_goal(user_id, goal):
        async with get_connection() as conn:
            await conn.execute("""UPDATE users SET goal = $1 WHERE user_id = $2""", goal, user_id)

    @staticmethod
    async def new_user(user_id, name, email, goal, steps):
        """Создать нового пользователя"""
        async with get_connection() as conn:
            await conn.execute("""
                INSERT INTO users (user_id, name, email, goal, everyday) 
                VALUES ($1, $2, $3, $4, 0)
            """, user_id, name, email, goal)
            for step in steps:
                print(step)
                await conn.execute("""
                    INSERT INTO steps (user_id, step) VALUES($1, $2)
                """, user_id, step)

    @staticmethod
    async def get_top_users():
        """Получить топ пользователей"""
        async with get_connection() as conn:
            return await conn.fetch("SELECT name, everyday FROM users ORDER BY everyday DESC")

    @staticmethod
    async def get_user_steps(user_id):
        """Получить steps по ID"""
        async with get_connection() as conn:
            return await conn.fetch("SELECT * FROM steps WHERE user_id = $1", user_id)

    @staticmethod
    async def get_step(step_id):
        """Получить step по ID"""
        async with get_connection() as conn:
            return await conn.fetchrow("SELECT * FROM steps WHERE step_id = $1", step_id)


    # Pomodoro методы
    @staticmethod
    async def get_pomodoro_session(user_id, event_id):
        """Получить сессию Pomodoro"""
        async with get_connection() as conn:
            return await conn.fetchrow("""
                SELECT * FROM pomodoro_sessions 
                WHERE user_id = $1 AND event_id = $2
            """, user_id, event_id)

    @staticmethod
    async def save_pomodoro_session(session_data):
        """Сохранить сессию Pomodoro"""
        async with get_connection() as conn:
            await conn.execute("""
                INSERT INTO pomodoro_sessions 
                (user_id, event_id, work_duration, break_duration, long_break_duration,
                 pomodoros_completed, is_working, is_break, time_remaining, end_time, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id, event_id) DO UPDATE SET
                work_duration = EXCLUDED.work_duration,
                break_duration = EXCLUDED.break_duration,
                long_break_duration = EXCLUDED.long_break_duration,
                pomodoros_completed = EXCLUDED.pomodoros_completed,
                is_working = EXCLUDED.is_working,
                is_break = EXCLUDED.is_break,
                time_remaining = EXCLUDED.time_remaining,
                end_time = EXCLUDED.end_time,
                updated_at = CURRENT_TIMESTAMP
            """,
                               session_data['user_id'], session_data['event_id'],
                               session_data['work_duration'], session_data['break_duration'],
                               session_data['long_break_duration'], session_data['pomodoros_completed'],
                               session_data['is_working'], session_data['is_break'],
                               session_data['time_remaining'], session_data['end_time'])

    @staticmethod
    async def delete_pomodoro_session(user_id, event_id):
        """Удалить сессию Pomodoro"""
        async with get_connection() as conn:
            await conn.execute("""
                DELETE FROM pomodoro_sessions 
                WHERE user_id = $1 AND event_id = $2
            """, user_id, event_id)

    @staticmethod
    async def get_user_active_sessions(user_id):
        """Получить активные сессии пользователя"""
        async with get_connection() as conn:
            return await conn.fetch("""
                SELECT * FROM pomodoro_sessions 
                WHERE user_id = $1 AND (is_working = TRUE OR is_break = TRUE)
            """, user_id)

    @staticmethod
    async def cleanup_expired_sessions():
        """Очистить истекшие сессии"""
        async with get_connection() as conn:
            await conn.execute("""
                UPDATE pomodoro_sessions 
                SET is_working = FALSE, is_break = FALSE, time_remaining = 0
                WHERE end_time < CURRENT_TIMESTAMP AND (is_working = TRUE OR is_break = TRUE)
            """)

    @staticmethod
    async def update_pomodoro_stats(user_id, event_id, work_duration):
        """Обновить статистику Pomodoro"""
        async with get_connection() as conn:
            await conn.execute("""
                INSERT INTO pomodoro_stats 
                (user_id, event_id, pomodoros_completed, total_work_time, last_session)
                VALUES ($1, $2, 1, $3, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id, event_id) DO UPDATE SET
                pomodoros_completed = pomodoro_stats.pomodoros_completed + 1,
                total_work_time = pomodoro_stats.total_work_time + $3,
                last_session = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            """, user_id, event_id, work_duration)

    @staticmethod
    async def get_user_pomodoro_stats(user_id):
        """Получить статистику Pomodoro пользователя"""
        async with get_connection() as conn:
            result = await conn.fetchrow("""
                SELECT 
                    COALESCE(SUM(pomodoros_completed), 0) as total_pomodoros,
                    COALESCE(SUM(total_work_time), 0) as total_work_time,
                    COUNT(DISTINCT event_id) as total_events,
                    MAX(last_session) as last_session
                FROM pomodoro_stats 
                WHERE user_id = $1
            """, user_id)

            return {
                'total_pomodoros': result['total_pomodoros'],
                'total_work_time': result['total_work_time'],
                'total_events': result['total_events'],
                'last_session': result['last_session']
            }

    @staticmethod
    async def get_event_pomodoro_stats(user_id, event_id):
        """Получить статистику Pomodoro для конкретного события"""
        async with get_connection() as conn:
            return await conn.fetchrow("""
                SELECT * FROM pomodoro_stats 
                WHERE user_id = $1 AND event_id = $2
            """, user_id, event_id)

    @staticmethod
    async def get_user_events_with_pomodoro(user_id):
        """Получить события пользователя с информацией о Pomodoro"""
        async with get_connection() as conn:
            return await conn.fetch("""
                SELECT 
                    ps.event_id,
                    ps.pomodoros_completed,
                    ps.updated_at as last_activity,
                    COALESCE(pstats.total_work_time, 0) as total_work_time
                FROM pomodoro_sessions ps
                LEFT JOIN pomodoro_stats pstats ON ps.user_id = pstats.user_id AND ps.event_id = pstats.event_id
                WHERE ps.user_id = $1
                ORDER BY ps.updated_at DESC
            """, user_id)


async def main():
    await init_db()
    dbase = Dbase()

    # Пример использования Pomodoro методов
    try:
        # Тестируем создание сессии
        session_data = {
            'user_id': 123456,
            'event_id': 1,
            'work_duration': 1500,
            'break_duration': 300,
            'long_break_duration': 900,
            'pomodoros_completed': 0,
            'is_working': True,
            'is_break': False,
            'time_remaining': 1500,
            'end_time': datetime.now()
        }

        await dbase.save_pomodoro_session(session_data)
        print("✅ Сессия Pomodoro создана")

        # Получаем статистику
        stats = await dbase.get_user_pomodoro_stats(123456)
        print(f"📊 Статистика: {stats}")

    except Exception as e:
        print(f"❌ Ошибка: {e}")


if __name__ == '__main__':
    asyncio.run(main())