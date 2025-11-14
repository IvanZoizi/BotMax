import asyncio
from typing import Callable, Dict, Any, Awaitable


from maxapi.context import MemoryContext
from maxapi import Bot, Dispatcher, Router, F
from maxapi.context import StatesGroup, State
from maxapi.filters.command import Command
from maxapi.types import Message, MessageCreated, BotStarted, MessageCallback
from pydantic.v1.validators import anystr_strip_whitespace

from config import token
from utils import dbase, RegistrationStates
from handlers import routers, scheduler, notification_settings, reminder_notification
from utils import *
from utils.dbase import init_db

bot = Bot(token=token)
dp = Dispatcher()


class UserMiddleware:
    """Middleware для добавления user_id в контекст всех обработчиков"""

    async def __call__(
            self,
            handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
            event: Any,
            data: Dict[str, Any]
    ) -> Any:
        # Получаем user_id из события
        user_id = None
        if hasattr(event, 'from_user') and hasattr(event.from_user, 'user_id'):
            user_id = event.from_user.user_id
        elif hasattr(event, 'user_id'):
            user_id = event.user_id
        elif hasattr(event, 'chat_id'):
            user_id = event.chat_id
        if not await Dbase.get_user_entrance(user_id):
            await Dbase.new_user_entrance(user_id)
            await Dbase.new_day_user(user_id)

        return await handler(event, data)


@dp.bot_started()
async def bot_started(event: BotStarted, context: MemoryContext):
    if await Dbase.get_user(event.from_user.user_id):
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
    if await Dbase.get_user(event.from_user.user_id):
        await event.message.answer("""Рад снова вас видеть! Чем займёмся сегодня? 😊""",
                                   attachments=[start_kb()])
    else:
        mes = await event.message.answer("""
🤖 Добро пожаловать в бот продуктивности "Фокус"!

Здесь вы сможете:
• Ставить цели и задачи
• Использовать технику Pomodoro
• Отслеживать привычки
• Получать персональные рекомендации

Для начала работы необходимо зарегистрироваться!
Введите ваше имя!""")
        await context.update_data(message=mes.message)
        await context.set_state(RegistrationStates.waiting_for_name)


@dp.message_created(F.callback.payload == 'start')
async def hello(call: MessageCallback):
    await call.message.delete()
    await call.message.answer("""Рад снова вас видеть! Чем займёмся сегодня? 😊""",
                                   attachments=[start_kb()])



async def main():
    """Основная функция запуска бота"""
    await init_db()
    dp.include_routers(*routers)
    dp.middleware(UserMiddleware())
    data = await Dbase.get_all_notification()
    for i in data:
        hours, minutes = list(map(int, i[3].split(":")))
        scheduler.add_job(
                func=notification_settings,
                trigger='cron',
                minute=minutes,
                hour=hours,
                id=i[4],
                args=(bot, i[3],)
        )
    scheduler.add_job(
        func=reminder_notification,
        trigger='cron',
        minute=0,
        hour=12,
        args=(bot,)
    )
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