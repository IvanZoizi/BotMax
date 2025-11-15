from maxapi import Router, types, F
from maxapi.context import MemoryContext
from maxapi.enums.parse_mode import ParseMode
from maxapi.types import MessageCreated, MessageCallback
from datetime import datetime

from utils import *

users_routers = Router()


def format_days_with_us(created_at):
    """Форматирование времени с нами в читаемом виде"""
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))

    now = datetime.now()
    delta = now - created_at

    days = delta.days
    months = days // 30
    years = days // 365

    if years > 0:
        return f"{years} {get_plural(years, 'год', 'года', 'лет')}"
    elif months > 0:
        return f"{months} {get_plural(months, 'месяц', 'месяца', 'месяцев')}"
    else:
        return f"{days} {get_plural(days, 'день', 'дня', 'дней')}"


def get_plural(number, form1, form2, form5):
    """Функция для правильного склонения слов"""
    n = abs(number) % 100
    n1 = n % 10
    if 10 < n < 20:
        return form5
    if n1 == 1:
        return form1
    if 1 < n1 < 5:
        return form2
    return form5


@users_routers.message_callback(F.callback.payload == 'profile')
async def end_to_step(call: MessageCallback):
    await call.message.delete()
    user = await Dbase.get_user(call.from_user.user_id)

    # Форматируем время с нами
    days_with_us = format_days_with_us(user[6])  # created_at находится в 6-м элементе

    await call.message.answer(f"""🌟 **Ваш профиль**

👤 **Имя:** {user[1]}
📧 **Email:** {user[2]}
🎯 **Цель:** {user[3]}
📅 **С нами уже:** {days_with_us}
🔥 **Активная серия:** {user[5]} {get_plural(user[5], 'день', 'дня', 'дней')} подряд

💫 Продолжайте двигаться к своим целям! Каждый день — это новая возможность стать лучше.""",
                              parse_mode=ParseMode.MARKDOWN, attachments=[start_kb()])


@users_routers.message_callback(F.callback.payload == 'top')
async def end_to_step(call: MessageCallback):
    await call.message.delete()
    users = await Dbase.get_top_users()
    text = "🏆 **Топ самых продуктивных пользователей:**\n\n"
    for count, user in enumerate(users):
        emoji = ["🥇", "🥈", "🥉"][count] if count < 3 else f"{count + 1}️⃣"
        text += f"{emoji} {user[0]} — {user[1]} дней\n"

    text += "\n💪 Ваше имя тоже может быть здесь! Продолжайте работать над своими целями."

    await call.message.answer(text, parse_mode=ParseMode.MARKDOWN, attachments=[start_kb()])


@users_routers.message_callback(F.callback.payload == 'update_goals')
async def update_goals(call: MessageCallback, context: MemoryContext):
    await context.set_state(UpdateUserGoalsStates.goals)
    await call.message.delete()
    await call.message.answer("🎯 Напишите новую цель, к которой вы хотите прийти:")


@users_routers.message_created(UpdateUserGoalsStates.goals)
async def process_goal(event: MessageCreated, context: MemoryContext):
    goal = event.message.body.text.strip()

    if len(goal) < 10:
        await event.message.answer(
            "❌ Слишком короткое описание цели!\n\n"
            "📝 Распишите вашу мечту более подробно (минимум 10 символов). "
            "Чем детальнее вы опишете цель, тем легче будет построить путь к её достижению.\n\n"
            "💫 Пример хорошей цели: \"Хочу научиться свободно говорить на английском языке, "
            "чтобы уверенно чувствовать себя в путешествиях и читать профессиональную литературу\""
        )
        return

    if len(goal) > 500:
        await event.message.answer(
            "❌ Слишком длинное описание цели!\n\n"
            "📝 Сформулируйте цель более кратко (максимум 500 символов), "
            "сохранив главную суть и вдохновение."
        )
        return

    await context.update_data(goal=goal, steps=[])

    await event.message.answer(
        "✨ Отличная цель! Теперь превратим её в конкретный план действий.\n\n"
        "📝 **Добавьте первый шаг к вашей цели:**\n\n"
        "💡 **Примеры эффективных шагов:**\n"
        "• Составлять план на день каждое утро\n"
        "• Читать 15 минут профессиональной литературы в день\n"
        "• Делать 10-минутную зарядку ежедневно\n"
        "• Освоить технику Pomodoro для продуктивной работы\n"
        "• Медитировать 5 минут перед сном\n\n"
        "🎯 Добавляйте шаги последовательно — так большая цель станет легко достижимой!",
        parse_mode=ParseMode.MARKDOWN
    )
    await context.set_state(UpdateUserGoalsStates.steps)


@users_routers.message_created(UpdateUserGoalsStates.steps)
async def get_step(event: MessageCreated, context: MemoryContext):
    step = event.message.body.text.strip()

    if len(step) < 5:
        await event.message.answer(
            "❌ Слишком короткое описание шага!\n\n"
            "📝 Опишите шаг более подробно (минимум 5 символов). \n"
            "🎯 Помните: конкретный шаг = конкретный результат!\n\n"
            "💡 Пример хорошего шага: \"Читать 20 страниц книги по саморазвитию каждый вечер\""
        )
        return

    data = await context.get_data()
    steps = data['steps']
    steps.append(step)

    current_step_count = len(steps)

    await event.message.answer(
        f"✅ **Шаг {current_step_count} успешно добавлен!**\n\n"
        f"📋 **Ваш план действий ({current_step_count} шагов):**\n" +
        "\n".join([f"• {s}" for s in steps]) +
        f"\n\n🎯 Продолжайте добавлять шаги или завершите планирование:",
        attachments=[steps_for_update_kb()], parse_mode=ParseMode.MARKDOWN
    )


@users_routers.message_callback(F.callback.payload == 'end_to_step_update')
async def end_to_step(call: MessageCallback, context: MemoryContext):
    await call.message.delete()

    data = await context.get_data()
    await context.clear()

    await Dbase.new_goal(call.from_user.user_id, data['goal'])
    await Dbase.new_steps(call.from_user.user_id, data['steps'])

    welcome_message = """✨ **Цель успешно обновлена!**

🎯 Теперь у вас есть четкий план действий. Помните:
• Маленькие шаги каждый день приводят к большим результатам
• Регулярность — ключ к успеху
• Отмечайте свои прогрессы

💫 Вперёд к новым достижениям! Ваш будущий я будет благодарен вам за усилия сегодня."""

    await call.message.answer(welcome_message, parse_mode=ParseMode.MARKDOWN, attachments=[start_kb()])