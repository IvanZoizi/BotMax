from contextlib import asynccontextmanager

import asyncpg
import asyncio
from config import DB_USER, DB_PASSWORD, DB_HOST,DB_PORT, DB_NAME


async def init_db():
    """Инициализация пула подключений для пользователей"""
    global _user_pool
    if _user_pool is None:
        # ssl_context = ssl.create_default_context(cafile="/etc/ssl/postgres.crt")
        # ssl_context.check_hostname = False
        # ssl_context.verify_mode = ssl.CERT_REQUIRED

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

        # async with _user_pool.acquire() as conn:
        #     # Таблица для пользователей
        #     await conn.execute(
        #         """
        #     """
        #     )


@asynccontextmanager
async def get_connection():
    """Асинхронный контекстный менеджер для подключений к БД пользователей"""
    if _user_pool is None:
        await init_db()
    async with _user_pool.acquire() as conn:
        yield conn


class Dbase:
    @staticmethod
    async def get_user(self, user_id):
        """Получить пользователя по ID"""
        return await self.conn.fetchrow("""SELECT * FROM users WHERE user_id = $1""", user_id)

    @staticmethod
    async def new_user(self, user_id, name, email, goal, steps):
        """Создать нового пользователя"""
        await self.conn.execute("""
            INSERT INTO users (user_id, name, email, goal, steps, everyday) 
            VALUES ($1, $2, $3, $4, $5, 0)
        """, user_id, name, email, goal, steps)

    @staticmethod
    async def get_top_users(self):
        """Получить топ пользователей"""
        return await self.conn.fetch("""SELECT name, everyday FROM users ORDER BY everyday DESC""")


async def main():
    dbase = Dbase()
    # Пример использования
    top_users = await dbase.get_top_users()
    print(top_users)



if __name__ == '__main__':
    asyncio.run(main())