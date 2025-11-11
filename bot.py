import asyncio

from maxapi.context import MemoryContext
from maxapi import Bot, Dispatcher, Router, F
from maxapi.context import StatesGroup, State
from maxapi.filters.command import Command
from maxapi.types import Message, MessageCreated, BotStarted

from config import token
from utils import dbase, RegistrationStates
from handlers import routers
from utils import *

bot = Bot(token=token)
dp = Dispatcher()


@dp.bot_started()
async def bot_started(event: BotStarted, context: MemoryContext):
    print(await bot.get_chat_by_id(88815894))
    print(event.user.user_id)
    if dbase.get_user(event.from_user.user_id):
        await event.message.answer("""Рад снова вас видеть! Чем займёмся сегодня? 😊""",
                                   attachments=[start_kb()])
    else:
        await event.message.answer("""
🤖 Добро пожаловать в бот продуктивности "Фокус"!

Здесь вы сможете:
• Ставить цели и задачи
• Использовать технику Pomodoro
• Отслеживать привычки
• Получать персональные рекомендации

Для начала работы необходимо зарегистрироваться!
Введите ваше имя!""")
        await context.set_state(RegistrationStates.waiting_for_name)

@dp.message_created(Command('start'))
async def hello(event: MessageCreated, context: MemoryContext):
    print(await bot.get_chat_by_id(88815894))
    if dbase.get_user(event.from_user.user_id):
        await event.message.answer("""Рад снова вас видеть! Чем займёмся сегодня? 😊""",
                                   attachments=[start_kb()])
    else:
        await event.message.answer("""
🤖 Добро пожаловать в бот продуктивности "Фокус"!

Здесь вы сможете:
• Ставить цели и задачи
• Использовать технику Pomodoro
• Отслеживать привычки
• Получать персональные рекомендации

Для начала работы необходимо зарегистрироваться!
Введите ваше имя!""")
        await context.set_state(RegistrationStates.waiting_for_name)



async def main():
    """Основная функция запуска бота"""
    dp.include_routers(*routers)

    print("Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())


# import asyncio
# import logging
#
# from maxapi import Bot, Dispatcher
# from maxapi.types import BotStarted, Command, MessageCreated
#
# logging.basicConfig(level=logging.INFO)
#
# bot = Bot('f9LHodD0cOL8I42VUpR9-7WcCKp1WvtyPFrSz1PvS1jRNRdlkYTRpIb2vby-HfRqWbkuT1UF-3MJFhYFuR1g')
# dp = Dispatcher()
#
# # Ответ бота при нажатии на кнопку "Начать"
# @dp.bot_started()
# async def bot_started(event: BotStarted):
#     await event.bot.send_message(
#         chat_id=event.chat_id,
#         text='Привет! Отправь мне /start'
#     )
#
# # Ответ бота на команду /start
# @dp.message_created(Command('start'))
# async def hello(event: MessageCreated):
#     await event.message.answer(f"Пример чат-бота для MAX 💙")
#
#
# async def main():
#     await dp.start_polling(bot)
#
#
# if __name__ == '__main__':
#     asyncio.run(main())