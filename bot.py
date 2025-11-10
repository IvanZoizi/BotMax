import asyncio
from maxapi import Bot, Dispatcher, Router, F
from maxapi.context import StatesGroup, State
from maxapi.types import Message
from config import token
from utils import Dbase

router = Router()

async def main():
    """Основная функция запуска бота"""
    # Замените на ваш токен
    dbase = Dbase("./db.sqlite")
    bot = Bot(token=token)
    dp = Dispatcher()
    # Подключаем роутер
    dp.include_router(router)

    print("Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())