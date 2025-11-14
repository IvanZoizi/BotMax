# notification.py
import datetime
import random
import re

from aiofiles.os import replace
from maxapi import Router, types, F, Bot
from maxapi.context import MemoryContext
from maxapi.enums.parse_mode import ParseMode
from maxapi.types import MessageCreated, MessageCallback
from apscheduler.schedulers.background import BackgroundScheduler

from utils import *

not_router = Router()

scheduler = BackgroundScheduler()
scheduler.start()


async def notification_settings(bot, time_setting):
    """Функция отправки уведомлений пользователям"""
    data = await Dbase.get_user_notification_by_time(time_setting)

    day_now = datetime.datetime.now().weekday() + 1

    # Расширенный список текстов для сообщений
    texts_from_message = [
        "🎯 Пора выполнять задания! Не откладывай на потом",
        "⏰ Время действовать! Твои цели ждут тебя",
        "🚀 Настал момент для продуктивности!",
        "💫 Идеальное время для выполнения задач",
        "🌟 Не забывай про свои цели! Самое время поработать над ними",
        "📝 Планируешь достигать успеха? Тогда начинай сейчас!",
        "🔥 День для великих свершений! Приступай к заданиям"
    ]

    # Расширенный список текстов для кнопок
    texts_from_kb = [
        "Давай приступать! 🚀",
        "Начать сейчас! 💪",
        "К делу! 🎯",
        "Погнали! ⚡",
        "Приступить к заданиям 📝",
        "Время действовать! ⏰"
    ]

    for i in data:
        if int(i[2]) == int(day_now):
            try:
                selected_text = random.choice(texts_from_message)
                selected_button = random.choice(texts_from_kb)

                await bot.send_message(
                    chat_id=i[1],
                    text=selected_text,
                    attachments=[make_mail_user_kb(selected_button)]
                )
                print(f"Уведомление отправлено пользователю {i[1]} в {time_setting}")

            except Exception as ex:
                print(f"Ошибка отправки уведомления пользователю {i[1]}: {ex}")


async def reminder_notification(bot):
    # Пользователи, которых не было 1 день
    data = await Dbase.get_last_day_users(1)
    for user in data:
        try:
            await bot.send_message(
                chat_id=user[0],
                text="Привет! Тебя не было всего день, но мы уже успели соскучиться 😊\nЗаходи проверить свои цели и прогресс!",
            )
        except:
            pass

    # Пользователи, которых не было 3 дня
    data = await Dbase.get_last_day_users(3)
    for user in data:
        try:
            await bot.send_message(
                chat_id=user[0],
                text="Эй, давно тебя не было! Твой бонус может скоро пропасть 🎁\nНе упусти свою награду - заходи сегодня!",
            )
        except:
            pass

    # Пользователи, которых не было 5 дней (сброс бонуса)
    data = await Dbase.get_last_day_users(5)
    for user in data:
        try:
            await Dbase.set_everyday_user(user[0], 0)
            await bot.send_message(
                chat_id=user[0],
                text="К сожалению, твой бонус сгорел из-за отсутствия 😔\nНо ты можешь начать собирать его заново - просто вернись!",
            )
        except:
            pass

    # Пользователи, которых не было 7 дней
    data = await Dbase.get_last_day_users(7)
    for user in data:
        try:
            await bot.send_message(
                chat_id=user[0],
                text="Целую неделю тебя нет! Твои цели ждут тебя 🎯\nЗаходи, посмотри что нового и продолжи свой путь к успеху!",
            )
        except:
            pass

def validate_time_format(time_str):
    """Проверка корректности формата времени HH:MM"""
    time_pattern = r'^([0-1]?[0-9]|2[0-3]):([0-5][0-9])$'
    return re.match(time_pattern, time_str) is not None


@not_router.message_callback(F.callback.payload == 'notification')
async def notification(call: MessageCallback):
    """Главное меню уведомлений"""
    await call.message.delete()
    await call.message.answer(
        "Раздел уведомлений\n\n"
        "Здесь ты можешь настроить напоминания о своих задачах и целях. "
        "Выбери подходящее время, и бот будет присылать тебе мотивирующие сообщения!",
        attachments=[notification_kb()]
    )


@not_router.message_callback(F.callback.payload == 'new_notification')
async def notification(call: MessageCallback, context: MemoryContext):
    """Начало создания нового уведомления"""
    await context.update_data(days=[])
    await call.message.delete()
    await call.message.answer(
        "Выбери дни недели для уведомлений\n\n"
        "Отметь дни, когда хочешь получать напоминания. "
        "Можно выбрать несколько дней!",
        attachments=[set_days_kb([])]
    )


@not_router.message_callback(F.callback.payload.startswith('set_day'))
async def notification(call: MessageCallback, context: MemoryContext):
    """Обработка выбора дней недели"""
    data = await context.get_data()
    id_day = int(call.callback.payload.split("_")[-1])

    if id_day not in data['days']:
        data['days'].append(id_day)
        action = "добавлен"
    else:
        data['days'].remove(id_day)
        action = "удален"

    await context.update_data(days=data['days'])
    await call.message.delete()

    days_text = ", ".join([dict_days[day] for day in sorted(data['days'])]) if data['days'] else "пока не выбраны"

    await call.message.answer(
        f"Выбор дней недели\n\n"
        f"Выбранные дни: {days_text}\n"
        f"Последнее действие: {dict_days[id_day]} {action}\n\n"
        f"Нажми 'Подтвердить' когда закончишь выбор",
        attachments=[set_days_kb(data['days'])]
    )


@not_router.message_callback(F.callback.payload == 'accept_days')
async def notification(call: MessageCallback, context: MemoryContext):
    """Подтверждение выбранных дней и запрос времени"""
    data = await context.get_data()
    await call.message.delete()

    if not data['days']:
        await call.message.answer(
            "Не выбраны дни недели\n\n"
            "Пожалуйста, выбери хотя бы один день для уведомлений",
            attachments=[set_days_kb([])]
        )
        return

    selected_days = ", ".join([dict_days[day] for day in sorted(data['days'])])

    await context.set_state(NotificationState.set_time)
    await call.message.answer(
        f"Установка времени уведомлений\n\n"
        f"Выбранные дни: {selected_days}\n\n"
        "Введи время в формате ЧАСЫ:МИНУТЫ\n"
        "Например: 09:00 или 18:30\n\n"
        "Время должно быть в 24-часовом формате"
    )


@not_router.message_created(NotificationState.set_time)
async def set_time(event: MessageCreated, context: MemoryContext):
    """Обработка ввода времени для уведомлений"""
    # Проверка формата времени
    if not validate_time_format(event.message.body.text):
        await event.message.answer(
            "Неверный формат времени!\n\n"
            "Пожалуйста, введи время в формате ЧАСЫ:МИНУТЫ\n"
            "Например: 09:00, 14:30, 18:45\n\n"
            "Используй 24-часовой формат"
        )
        return

    data = await context.get_data()
    count = 0
    failed_count = 0

    for day in data['days']:
        cron_id = f"{event.from_user.user_id}:{day}:{event.message.body.text}"

        if not await Dbase.check_user_notification(cron_id):
            try:
                hours, minutes = list(map(int, event.message.body.text.split(":")))

                # Дополнительная проверка валидности времени
                if hours < 0 or hours > 23 or minutes < 0 or minutes > 59:
                    raise ValueError("Некорректное время")

                scheduler.add_job(
                    func=notification_settings,
                    trigger='cron',
                    minute=minutes,
                    hour=hours,
                    id=cron_id,
                    args=(event.bot, event.message.body.text,)
                )
                await Dbase.new_notification(event.from_user.user_id, day, cron_id, event.message.body.text)
                count += 1

            except Exception as e:
                print(f"Ошибка при создании уведомления на день {day}: {e}")
                failed_count += 1
        else:
            failed_count += 1

    await context.clear()

    if count > 0:
        success_text = (
            f"Уведомления успешно созданы!\n\n"
            f"Добавлено: {count} уведомлений\n"
            f"Время: {event.message.body.text}\n"
            f"Дни: {', '.join([dict_days[day] for day in sorted(data['days'])])}\n\n"
            f"Теперь ты будешь получать напоминания в выбранное время!"
        )
    else:
        success_text = (
            f"Не удалось создать уведомления\n\n"
            f"Возможно, такие уведомления уже существуют или произошла ошибка.\n"
            f"Попробуй создать уведомление с другими параметрами."
        )

    await event.message.answer(success_text, attachments=[notification_kb()])


@not_router.message_callback(F.callback.payload.startswith('my_notification'))
async def my_notification(call: MessageCallback):
    """Просмотр существующих уведомлений"""
    data = await Dbase.get_users_notification(call.from_user.user_id)
    page_num = int(call.callback.payload.split("_")[-1])

    await call.message.delete()

    if not data:
        await call.message.answer(
            "У тебя пока нет уведомлений\n\n"
            "Создай свое первое уведомление, чтобы не забывать о важных задачах!",
            attachments=[notification_kb()]
        )
        return

    total_count = len(data)
    await call.message.answer(
        f"Твои уведомления\n\n"
        f"Всего уведомлений: {total_count}\n"
        f"Страница {page_num + 1}/{(total_count + 7) // 8}",
        attachments=[my_notification_kb(data, page_num)]
    )


@not_router.message_callback(F.callback.payload.startswith('get_notification_'))
async def my_notification(call: MessageCallback):
    """Просмотр деталей конкретного уведомления"""
    id_not = int(call.callback.payload.split("_")[-1])
    notification = await Dbase.get_user_notification_by_id(id_not)

    await call.message.delete()

    if notification:
        await call.message.answer(
            f"Настройки уведомления\n\n"
            f"День: {dict_days[notification[2]]}\n"
            f"Время: {notification[3]}\n"
            f"ID: {notification[4]}\n\n"
            f"Выбери действие:",
            attachments=[get_notification_kb(id_not)]
        )
    else:
        await call.message.answer(
            "Уведомление не найдено",
            attachments=[notification_kb()]
        )


@not_router.message_callback(F.callback.payload.startswith('delete_notification_'))
async def my_notification(call: MessageCallback):
    """Удаление уведомления"""
    id_not = int(call.callback.payload.split("_")[-1])
    notification = await Dbase.get_user_notification_by_id(id_not)

    if notification:
        try:
            scheduler.remove_job(notification[4])
            print(f"Задание {notification[4]} удалено из планировщика")
        except Exception as ex:
            print(f"Задание не найдено в планировщике: {ex}")

        await Dbase.delete_notification(notification[0])
        await call.message.delete()
        await call.message.answer(
            "Уведомление успешно удалено!",
            attachments=[notification_kb()]
        )
    else:
        await call.message.answer(
            "Уведомление не найдено",
            attachments=[notification_kb()]
        )


@not_router.message_callback(F.callback.payload.startswith('update_notification_'))
async def my_notification(call: MessageCallback, context: MemoryContext):
    """Начало обновления времени уведомления"""
    id_not = int(call.callback.payload.split("_")[-1])
    notification = await Dbase.get_user_notification_by_id(id_not)

    if not notification:
        await call.message.answer("Уведомление не найдено")
        return

    await context.update_data(id_not=id_not)
    await context.set_state(NotificationState.update_time)
    await call.message.delete()
    await call.message.answer(
        f"Изменение времени уведомления\n\n"
        f"Текущие настройки:\n"
        f"День: {dict_days[notification[2]]}\n"
        f"Старое время: {notification[3]}\n\n"
        "Введи новое время в формате ЧАСЫ:МИНУТЫ\n"
        "Например: 09:00 или 18:30\n\n"
        "Время должно быть в 24-часовом формате"
    )


@not_router.message_created(NotificationState.update_time)
async def set_time(event: MessageCreated, context: MemoryContext):
    """Обработка обновления времени уведомления"""
    # Проверка формата времени
    if not validate_time_format(event.message.body.text):
        await event.message.answer(
            "Неверный формат времени!\n\n"
            "Пожалуйста, введи время в формате ЧАСЫ:МИНУТЫ\n"
            "Например: 09:00, 14:30, 18:45\n\n"
            "Используй 24-часовой формат\n\n"
            "Попробуй еще раз:"
        )
        return

    data = await context.get_data()
    notification = await Dbase.get_user_notification_by_id(data['id_not'])

    if not notification:
        await event.message.answer("Уведомление не найдено")
        await context.clear()
        return

    try:
        # Проверка валидности времени
        hours, minutes = list(map(int, event.message.body.text.split(":")))
        if hours < 0 or hours > 23 or minutes < 0 or minutes > 59:
            raise ValueError("Некорректное время")

        # Удаляем старое задание
        try:
            scheduler.remove_job(notification[4])
        except Exception as ex:
            print(f"Старое задание не найдено: {ex}")

        # Создаем новое задание
        cron_id = f"{event.from_user.user_id}:{notification[2]}:{event.message.body.text}"

        if not await Dbase.check_user_notification(cron_id):
            scheduler.add_job(
                func=notification_settings,
                trigger='cron',
                minute=minutes,
                hour=hours,
                id=cron_id,
                args=(event.bot, event.message.body.text,)
            )
            await Dbase.update_time_notification(notification[0], event.message.body.text, cron_id)

            await event.message.answer(
                f"Время уведомления обновлено!\n\n"
                f"День: {dict_days[notification[2]]}\n"
                f"Новое время: {event.message.body.text}\n\n"
                f"Теперь уведомление будет приходить в новое время!",
                attachments=[notification_kb()]
            )
        else:
            await event.message.answer(
                "Такое уведомление уже существует!\n\n"
                "Попробуй другое время или день",
                attachments=[notification_kb()]
            )

    except ValueError as e:
        await event.message.answer(
            "Некорректное время!\n\n"
            "Часы должны быть от 0 до 23, минуты от 0 до 59\n\n"
            "Попробуй еще раз:"
        )
        return
    except Exception as e:
        await event.message.answer(
            "Ошибка при обновлении уведомления\n\n"
            "Попробуй позже или обратись в поддержку",
            attachments=[notification_kb()]
        )

    await context.clear()