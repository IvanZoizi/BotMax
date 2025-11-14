# routers/pomodoro_router.py
from maxapi import Router, types, F
from maxapi.context import MemoryContext
from maxapi.enums.parse_mode import ParseMode
from maxapi.types import MessageCreated, MessageCallback
from maxapi.keyboard import InlineKeyboardBuilder, CallbackButton

from utils import *
from utils.pomodoro_session import PomodoroSession
import asyncio
from bot import bot

pomodoro_router = Router()
#TODO: дописать методы БД
#TODO: Добавить обработчики для паузы, возобновления, статуса и отмены
#TODO: проверить циклическую зависимость bot

async def get_event_name(event_id: int) -> str:
    """Получить название события по ID"""
    ### TODO: Написать билдер сообшение на step
    return f"Событие "

# Словарь для активных таймеров # TODO: подумать над другой реализацией
active_timers = {}


async def work_period_finished(user_id: int, event_id: int):
    """Колбэк завершения рабочего периода"""
    session = PomodoroSession(event_id, user_id)
    await session.load_from_db()

    await session.complete_pomodoro()
    await session.start_break()

    break_type = "длинный" if session.pomodoros_completed % 4 == 0 else "короткий"
    break_duration = session.long_break_duration if session.pomodoros_completed % 4 == 0 else session.break_duration

    #TODO ипортировать бота без циклической МБ все ок как минимум проверить

    await bot.send_message(
        user_id=user_id,
        message=f"✅ Рабочий период завершен!\n"
                f"🍅 Завершено помодоро: {session.pomodoros_completed}\n"
                f"☕ {break_type.capitalize()} перерыв: {break_duration // 60} мин\n"
                f"Нажмите /pomodoro_break чтобы начать перерыв"
    )


async def break_period_finished(user_id: int, event_id: int):
    """Колбэк завершения перерыва"""
    session = PomodoroSession(event_id, user_id)
    await session.load_from_db()

    session.is_break = False
    await session.save_to_db()


    await bot.send_message(
        user_id=user_id,
        message=f"🔄 Перерыв завершен!\nГотовы к следующему рабочему периоду?\n"
                f"Нажмите /pomodoro_work чтобы продолжить\n"
                f"🍅 Всего завершено: {session.pomodoros_completed}"
    )


@pomodoro_router.message_callback(F.callback.payload == 'pomodoro')
async def start_pomodoro(callback: MessageCallback, context: MemoryContext):
    user_id = callback.from_user.id
    user_steps = await Dbase.get_user_steps(user_id)

    if not user_steps:
        await callback.message.answer("У вас нет активных событий для работы по Pomodoro")
        return

    keyboard = InlineKeyboardBuilder()

    for step in user_steps:
        keyboard.row(CallbackButton(
            text=step['name'],
            payload=f"pomodoro_start:{step['step_id']}"
        ))

    await callback.message.answer(
        "Выберите событие для Pomodoro:",
        attachments=[keyboard.as_markup()]
    )


@pomodoro_router.message_callback(F.callback.payload.startswith('pomodoro_start:'))
async def start_pomodoro_session(callback: MessageCallback, context: MemoryContext):
    user_id = callback.from_user.id
    event_id = int(callback.callback.payload.split(':')[1])

    # Создаем и загружаем сессию
    session = PomodoroSession(event_id, user_id)
    await session.load_from_db()

    keyboard = InlineKeyboardBuilder()
    keyboard.row(CallbackButton(text="▶️ Старт", payload=f"pomodoro_work:{event_id}"))
    keyboard.row(CallbackButton(text="❌ Отмена", payload="pomodoro_cancel"))

    event_name = await get_event_name(event_id)

    await callback.message.edit(
        text=f"🍅 Готов к Pomodoro!\n"
             f"Событие: {event_name}\n"
             f"Работа: 25 мин\nПерерыв: 5 мин\n"
             f"После 4 подходов - длинный перерыв 15 мин\n"
             f"Завершено помодоро: {session.pomodoros_completed}",
        attachments=[keyboard.as_markup()]
    )


@pomodoro_router.message_callback(F.callback.payload.startswith('pomodoro_work:'))
async def start_work_period(callback: MessageCallback, context: MemoryContext):
    user_id = callback.from_user.id
    event_id = int(callback.callback.payload.split(':')[1])

    session = PomodoroSession(event_id, user_id)
    await session.load_from_db()
    await session.start_work()

    # Создаем асинхронный таймер
    timer_task = asyncio.create_task(
        pomodoro_timer(session.work_duration, user_id, event_id, work_period_finished)
    )

    # Сохраняем ссылку на таймер
    active_timers[(user_id, event_id)] = timer_task ##TODO: Может выбрать альтернативный вариант мб REDIS

    event_name = await get_event_name(event_id)

    keyboard = InlineKeyboardBuilder()
    keyboard.row(CallbackButton(text="⏸️ Пауза", payload=f"pomodoro_pause:{event_id}"))
    keyboard.row(CallbackButton(text="⏹️ Стоп", payload=f"pomodoro_stop:{event_id}"))

    await callback.message.edit(
        text=f"🎯 Рабочий период начался!\n"
             f"Событие: {event_name}\n"
             f"Время: 25 минут\n"
             f"Завершено помодоро: {session.pomodoros_completed}",
        attachments=[keyboard.as_markup()]
    )


async def pomodoro_timer(duration: int, user_id: int, event_id: int, callback):
    """Асинхронный таймер для pomodoro"""
    await asyncio.sleep(duration)
    await callback(user_id, event_id)

    # Удаляем таймер из активных
    active_timers.pop((user_id, event_id), None)


@pomodoro_router.message_callback(F.callback.payload.startswith('pomodoro_break:'))
async def start_break_period(callback: MessageCallback, context: MemoryContext):
    user_id = callback.from_user.id
    event_id = int(callback.callback.payload.split(':')[1])

    session = PomodoroSession(event_id, user_id)
    await session.load_from_db()

    if session.is_break:
        if session.pomodoros_completed % 4 == 0:
            duration = session.long_break_duration
            break_type = "длинный"
        else:
            duration = session.break_duration
            break_type = "короткий"

        await session.start_break()

        # Запускаем таймер перерыва
        timer_task = asyncio.create_task(
            pomodoro_timer(duration, user_id, event_id, break_period_finished)
        )
        active_timers[(user_id, event_id)] = timer_task

        await callback.message.answer(f"☕ Начался {break_type} перерыв! Отдохните {duration // 60} минут")



@pomodoro_router.message_callback(F.callback.payload == 'pomodoro_stats')
async def show_pomodoro_stats(callback: MessageCallback, context: MemoryContext):
    user_id = callback.from_user.id
    stats = await Dbase.get_user_pomodoro_stats(user_id) ## TODO: написать метод БД

    total_hours = stats['total_work_time'] // 3600
    total_minutes = (stats['total_work_time'] % 3600) // 60

    await callback.message.answer(
        f"📊 Ваша статистика Pomodoro:\n"
        f"🍅 Всего завершено помодоро: {stats['total_pomodoros']}\n"
        f"⏱️ Общее время работы: {total_hours}ч {total_minutes}м\n"
        f"📝 Событий с Pomodoro: {stats['total_events']}\n"
        f"🕒 Последняя сессия: {stats['last_session'] or 'еще не было'}"
    )

