import logging
from datetime import datetime, timedelta

from examples.keyboard.main import payload
from maxapi import Router, types, F
from maxapi.context import MemoryContext
from maxapi.enums.parse_mode import ParseMode
from maxapi.types import MessageCreated, MessageCallback, CallbackButton, RequestGeoLocationButton
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder

from utils import *
from utils.pomodoro_session import PomodoroSession
import asyncio
from bot import bot
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

pomodoro_router = Router()


async def get_event_name(event_id: int) -> str:
    """Получить название события по ID"""
    event = await Dbase.get_step(event_id)
    return f"{event['step']}"


# Словарь для активных таймеров
active_timers = {}
# Словарь для приостановленных таймеров
paused_timers = {}


async def work_period_finished(user_id: int, event_id: int):
    """Колбэк завершения рабочего периода"""
    logger.info("Work period finished")
    session = PomodoroSession(event_id, user_id)
    await session.load_from_db()

    await session.complete_pomodoro()

    break_type = "длинный" if session.pomodoros_completed % 4 == 0 else "короткий"
    break_duration = session.long_break_duration if session.pomodoros_completed % 4 == 0 else session.break_duration

    keyword = InlineKeyboardBuilder()
    keyword.row(CallbackButton(text="☕ Начать перерыв", payload=f"pomodoro_break:{event_id}"))
    await bot.send_message(
        user_id=user_id,
        text=f"✅ Рабочий период завершен!\n"
             f"🍅 Завершено помодоро: {session.pomodoros_completed}\n"
             f"☕ {break_type.capitalize()} перерыв: {break_duration // 60} мин\n",
        attachments=[keyword.as_markup()]
    )


async def break_period_finished(user_id: int, event_id: int):
    """Колбэк завершения перерыва"""
    session = PomodoroSession(event_id, user_id)
    await session.load_from_db()

    session.is_break = False
    await session.save_to_db()

    keyword = InlineKeyboardBuilder()
    keyword.row(CallbackButton(text="Продолжить работу", payload=f"pomodoro_work:{event_id}"))
    await bot.send_message(
        user_id=user_id,
        text=f"🔄 Перерыв завершен!\nГотовы к следующему рабочему периоду?\n"
             f"🍅 Всего завершено: {session.pomodoros_completed}",
        attachments=[keyword.as_markup()]
    )


@pomodoro_router.message_callback(F.callback.payload == 'pomodoro')
async def start_pomodoro(callback: MessageCallback, context: MemoryContext):
    user_id = callback.from_user.user_id
    user_steps = await Dbase.get_user_steps(user_id)
    if not user_steps:
        await callback.message.answer("У вас нет активных событий для работы по Pomodoro")
        return

    keyboard = InlineKeyboardBuilder()

    for step in user_steps:
        keyboard.row(CallbackButton(
            text=step['step'],
            payload=f"pomodoro_start:{step['step_id']}"
        ))

    await callback.message.answer(
        "Выберите событие для Pomodoro:",
        attachments=[keyboard.as_markup()]
    )


@pomodoro_router.message_callback(F.callback.payload.startswith('pomodoro_start:'))
async def start_pomodoro_session(callback: MessageCallback, context: MemoryContext):
    user_id = callback.from_user.user_id
    event_id = int(callback.callback.payload.split(':')[1])

    # Создаем и загружаем сессию
    session = PomodoroSession(event_id, user_id)
    await session.load_from_db()

    keyboard = InlineKeyboardBuilder()
    keyboard.row(CallbackButton(text="▶️ Старт", payload=f"pomodoro_work:{event_id}"))
    keyboard.row(CallbackButton(text="❌ Отмена", payload="pomodoro_cancel"))

    event_name = await get_event_name(event_id)
    await callback.message.delete()
    await callback.message.answer(
        text=f"🍅 Готов к Pomodoro!\n"
             f"Событие: {event_name}\n"
             f"Работа: 25 мин\nПерерыв: 5 мин\n"
             f"После 4 подходов - длинный перерыв 15 мин\n"
             f"Завершено помодоро: {session.pomodoros_completed}",
        attachments=[keyboard.as_markup()]
    )


@pomodoro_router.message_callback(F.callback.payload.startswith('pomodoro_work:'))
async def start_work_period(callback: MessageCallback, context: MemoryContext):
    user_id = callback.from_user.user_id
    event_id = int(callback.callback.payload.split(':')[1])

    session = PomodoroSession(event_id, user_id)
    await session.load_from_db()
    await session.start_work()

    # Создаем асинхронный таймер
    timer_task = asyncio.create_task(
        pomodoro_timer(session.work_duration, user_id, event_id, work_period_finished)
    )

    # Сохраняем ссылку на таймер
    active_timers[(user_id, event_id)] = timer_task

    event_name = await get_event_name(event_id)

    keyboard = InlineKeyboardBuilder()
    keyboard.row(CallbackButton(text="⏸️ Пауза", payload=f"pomodoro_pause:{event_id}"))
    keyboard.row(CallbackButton(text="⏹️ Стоп", payload=f"pomodoro_stop:{event_id}"))

    await callback.message.delete()
    await callback.message.answer(
        text=f"🎯 Рабочий период начался!\n"
             f"Событие: {event_name}\n"
             f"Время: 25 минут\n"
             f"Завершено помодоро: {session.pomodoros_completed}",
        attachments=[keyboard.as_markup()]
    )


@pomodoro_router.message_callback(F.callback.payload.startswith('pomodoro_pause:'))
async def pause_pomodoro(callback: MessageCallback, context: MemoryContext):
    user_id = callback.from_user.user_id
    event_id = int(callback.callback.payload.split(':')[1])

    # Получаем активный таймер
    timer_key = (user_id, event_id)
    if timer_key in active_timers:
        timer_task = active_timers[timer_key]

        # Отменяем таймер
        timer_task.cancel()

        # Сохраняем информацию о приостановленном таймере
        session = PomodoroSession(event_id, user_id)
        await session.load_from_db()

        # Вычисляем оставшееся время
        if session.end_time:
            remaining_time = (session.end_time - datetime.now()).total_seconds()
            if remaining_time > 0:
                paused_timers[timer_key] = {
                    'remaining_time': remaining_time,
                    'callback': work_period_finished if session.is_working else break_period_finished,
                    'is_working': session.is_working,
                    'is_break': session.is_break
                }

        # Обновляем состояние сессии
        session.is_paused = True
        await session.save_to_db()

        # Удаляем из активных таймеров
        del active_timers[timer_key]

        event_name = await get_event_name(event_id)

        keyboard = InlineKeyboardBuilder()
        keyboard.row(CallbackButton(text="▶️ Продолжить", payload=f"pomodoro_resume:{event_id}"))
        keyboard.row(CallbackButton(text="⏹️ Стоп", payload=f"pomodoro_stop:{event_id}"))

        await callback.message.delete()
        await callback.message.answer(
            text=f"⏸️ Pomodoro приостановлен\n"
                 f"Событие: {event_name}\n"
                 f"Завершено помодоро: {session.pomodoros_completed}\n"
                 f"Нажмите 'Продолжить' чтобы возобновить",
            attachments=[keyboard.as_markup()]
        )
    else:
        await callback.message.answer("❌ Активный Pomodoro не найден")


@pomodoro_router.message_callback(F.callback.payload.startswith('pomodoro_resume:'))
async def resume_pomodoro(callback: MessageCallback, context: MemoryContext):
    user_id = callback.from_user.user_id
    event_id = int(callback.callback.payload.split(':')[1])

    timer_key = (user_id, event_id)
    if timer_key in paused_timers:
        paused_data = paused_timers[timer_key]

        # Восстанавливаем сессию
        session = PomodoroSession(event_id, user_id)
        await session.load_from_db()
        session.is_paused = False
        session.is_working = paused_data['is_working']
        session.is_break = paused_data['is_break']
        session.end_time = datetime.now() + timedelta(seconds=paused_data['remaining_time'])
        await session.save_to_db()

        # Запускаем новый таймер с оставшимся временем
        timer_task = asyncio.create_task(
            pomodoro_timer(
                paused_data['remaining_time'],
                user_id,
                event_id,
                paused_data['callback']
            )
        )

        # Перемещаем в активные таймеры
        active_timers[timer_key] = timer_task
        del paused_timers[timer_key]

        event_name = await get_event_name(event_id)
        period_type = "рабочий" if paused_data['is_working'] else "перерыв"

        keyboard = InlineKeyboardBuilder()
        keyboard.row(CallbackButton(text="⏸️ Пауза", payload=f"pomodoro_pause:{event_id}"))
        keyboard.row(CallbackButton(text="⏹️ Стоп", payload=f"pomodoro_stop:{event_id}"))

        await callback.message.delete()
        await callback.message.answer(
            text=f"▶️ Pomodoro возобновлен\n"
                 f"Событие: {event_name}\n"
                 f"Период: {period_type}\n"
                 f"Завершено помодоро: {session.pomodoros_completed}",
            attachments=[keyboard.as_markup()]
        )
    else:
        await callback.message.answer("❌ Приостановленный Pomodoro не найден")


@pomodoro_router.message_callback(F.callback.payload.startswith('pomodoro_stop:'))
async def stop_pomodoro(callback: MessageCallback, context: MemoryContext):
    user_id = callback.from_user.user_id
    event_id = int(callback.callback.payload.split(':')[1])

    timer_key = (user_id, event_id)

    # Останавливаем активный таймер
    if timer_key in active_timers:
        timer_task = active_timers[timer_key]
        timer_task.cancel()
        del active_timers[timer_key]

    # Удаляем приостановленный таймер
    if timer_key in paused_timers:
        del paused_timers[timer_key]

    # Сбрасываем сессию
    session = PomodoroSession(event_id, user_id)
    await session.load_from_db()

    # Сохраняем статистику перед сбросом
    if session.pomodoros_completed > 0:
        await Dbase.save_pomodoro_statistics(
            user_id=user_id,
            event_id=event_id,
            pomodoros_completed=session.pomodoros_completed,
            total_work_time=session.pomodoros_completed * session.work_duration
        )

    # Сбрасываем сессию
    await session.reset_session()

    event_name = await get_event_name(event_id)

    keyboard = InlineKeyboardBuilder()
    keyboard.row(CallbackButton(text="🍅 Начать заново", payload=f"pomodoro_start:{event_id}"))
    keyboard.row(CallbackButton(text="📊 Статистика", payload="pomodoro_stats"))

    await callback.message.delete()
    await callback.message.answer(
        text=f"⏹️ Pomodoro остановлен\n"
             f"Событие: {event_name}\n"
             f"Завершено помодоро: {session.pomodoros_completed}\n"
             f"Вы можете начать новую сессию",
        attachments=[keyboard.as_markup()]
    )


@pomodoro_router.message_callback(F.callback.payload == 'pomodoro_cancel')
async def cancel_pomodoro(callback: MessageCallback, context: MemoryContext):
    await callback.message.delete()
    keyboard = InlineKeyboardBuilder()
    keyboard.row(CallbackButton(text="🍅 Начать заново", payload=f"pomodoro"))
    keyboard.row(CallbackButton(text="📊 Статистика", payload="pomodoro_stats"))
    await callback.message.answer(
        text="❌ Pomodoro отменен",
        attachments=[keyboard.as_markup()]
    )


async def pomodoro_timer(duration: int, user_id: int, event_id: int, callback):
    """Асинхронный таймер для pomodoro"""
    try:
        logger.info("Pomodoro timer started")
        await asyncio.sleep(duration)
        logger.info("Pomodoro timer ended")

        # Проверяем, не был ли таймер отменен
        if (user_id, event_id) in active_timers:
            await callback(user_id, event_id)
            logger.info("Pomodoro callback ended")

        # Удаляем таймер из активных
        active_timers.pop((user_id, event_id), None)
    except asyncio.CancelledError:
        logger.info("Pomodoro timer cancelled")
        raise


@pomodoro_router.message_callback(F.callback.payload.startswith('pomodoro_break:'))
async def start_break_period(callback: MessageCallback, context: MemoryContext):
    user_id = callback.from_user.user_id
    event_id = int(callback.callback.payload.split(':')[1])

    session = PomodoroSession(event_id, user_id)
    await session.load_from_db()

    if not session.is_break:
        if session.pomodoros_completed % 4 == 0:
            duration = session.long_break_duration
            break_type = "длинный"
        else:
            duration = session.break_duration
            break_type = "короткий"

        await session.start_break()
        logger.info("Pomodoro break timer task created")
        # Запускаем таймер перерыва
        timer_task = asyncio.create_task(
            pomodoro_timer(duration, user_id, event_id, break_period_finished)
        )
        active_timers[(user_id, event_id)] = timer_task

        keyboard = InlineKeyboardBuilder()
        keyboard.row(CallbackButton(text="⏸️ Пауза", payload=f"pomodoro_pause:{event_id}"))
        keyboard.row(CallbackButton(text="⏹️ Стоп", payload=f"pomodoro_stop:{event_id}"))

        await callback.message.answer(
            text=f"☕ Начался {break_type} перерыв!\n"
                 f"Отдохните {duration // 60} минут",
            attachments=[keyboard.as_markup()]
        )


@pomodoro_router.message_callback(F.callback.payload == 'pomodoro_stats')
async def show_pomodoro_stats(callback: MessageCallback, context: MemoryContext):
    user_id = callback.from_user.user_id
    stats = await Dbase.get_user_pomodoro_stats(user_id)

    total_hours = stats['total_work_time'] // 3600
    total_minutes = (stats['total_work_time'] % 3600) // 60

    await callback.message.answer(
        f"📊 Ваша статистика Pomodoro:\n"
        f"🍅 Всего завершено помодоро: {stats['total_pomodoros']}\n"
        f"⏱️ Общее время работы: {total_hours}ч {total_minutes}м\n"
        f"📝 Событий с Pomodoro: {stats['total_events']}\n"
        f"🕒 Последняя сессия: {stats['last_session'] or 'еще не было'}"
    )