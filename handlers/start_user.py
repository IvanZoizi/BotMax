from maxapi import Router, types, F
from maxapi.context import MemoryContext
from maxapi.enums.parse_mode import ParseMode
from maxapi.types import MessageCreated, MessageCallback

from utils import *

user_router = Router()


@user_router.message_created(RegistrationStates.waiting_for_name)
async def process_name(event: MessageCreated, context: MemoryContext):
    name = event.message.body.text.strip()

    if len(name) < 2:
        await event.message.answer(
            "❌ Имя слишком короткое! Давайте познакомимся поближе — введите ваше настоящее имя (минимум 2 символа):"
        )
        return

    if len(name) > 50:
        await event.message.answer(
            "❌ Имя слишком длинное! Пожалуйста, введите имя до 50 символов:"
        )
        return

    await context.update_data(name=name)

    await event.message.answer(
        f"🎉 Прекрасно, {name}!\n\n"
        "📧 Теперь введите ваш email адрес. \n"
        "Мы будем использовать его только для важных уведомлений и восстановления доступа — никакого спама!", parse_mode=ParseMode.MARKDOWN
    )
    await context.set_state(RegistrationStates.waiting_for_email)


@user_router.message_created(RegistrationStates.waiting_for_email)
async def process_email(event: MessageCreated, context: MemoryContext):
    email = event.message.body.text.strip().lower()

    if "@" not in email or "." not in email or len(email) < 5:
        await event.message.answer(
            "❌ Неверный формат email! Пожалуйста, введите корректный email адрес:\n\n"
            "📝 Примеры:\n"
            "• example@gmail.com\n"
            "• user@mail.ru\n"
            "• name@yandex.ru"
        )
        return

    await context.update_data(email=email)

    user_data = await context.get_data()
    name = user_data.get('name', 'друг')

    await event.message.answer(
        f"✨ Идеально, {name}!\n\n"
        "🎯 Теперь самое интересное — какую грандиозную цель вы хотите достичь \n"
        "с помощью нашего бота?\n\n"
        "💡 Примеры вдохновляющих целей:\n"
        "• Повысить личную продуктивность на 50% за месяц\n"
        "• Научиться эффективно планировать свой день\n"
        "• Развить 5 полезных привычек за 30 дней\n"
        "• Улучшить концентрацию и фокус внимания\n"
        "• Найти идеальный баланс между работой и отдыхом\n\n"
        "🌟 Опишите своими словами — это поможет нам создать персонализированную программу, которая приведет вас к успеху!", parse_mode=ParseMode.MARKDOWN
    )
    await context.set_state(RegistrationStates.waiting_for_goal)


@user_router.message_created(RegistrationStates.waiting_for_goal)
async def process_goal(event: MessageCreated, context: MemoryContext):
    goal = event.message.body.text.strip()

    if len(goal) < 10:
        await event.message.answer(
            "❌ Слишком короткое описание цели! Распишите вашу мечту более подробно "
            "(минимум 10 символов). Чем детальнее вы опишете цель, тем лучше мы сможем вам помочь:\n\n"
            "🌟 Помните: большие цели достигаются маленькими шагами!"
        )
        return

    if len(goal) > 500:
        await event.message.answer(
            "❌ Слишком длинное описание! Сформулируйте цель более кратко "
            "(максимум 500 символов), но сохраните вдохновение:"
        )
        return

    await context.update_data(goal=goal, steps=[])

    await event.message.answer(
        "🚀 Потрясающая цель! Теперь давайте превратим ее в конкретный план действий.\n\n"
        "📝 Добавьте первый шаг к вашей цели:\n\n"
        "💪 Примеры эффективных шагов:\n"
        "• Составлять план на день каждое утро\n"
        "• Читать 15 минут в день по профессиональной литературе\n"
        "• Делать 10-минутную зарядку ежедневно\n"
        "• Освоить технику Pomodoro для работы\n"
        "• Медитировать 5 минут перед сном\n\n"
        "🎯 Добавляйте шаги один за другим — так большая цель станет легко достижимой!", parse_mode=ParseMode.MARKDOWN
    )
    await context.set_state(RegistrationStates.waiting_for_step)


@user_router.message_created(RegistrationStates.waiting_for_step)
async def get_step(event: MessageCreated, context: MemoryContext):
    step = event.message.body.text.strip()

    if len(step) < 5:
        await event.message.answer(
            "❌ Слишком короткое описание шага! Опишите шаг более подробно (минимум 5 символов). \n"
            "🎯 Помните: конкретный шаг = конкретный результат!"
        )
        return

    data = await context.get_data()
    steps = data['steps']
    steps.append(step)

    current_step_count = len(steps)

    await event.message.answer(
        f"✅ Шаг {current_step_count} успешно добавлен!\n\n"
        f"📋 Ваш план действий ({current_step_count} шагов):\n" +
        "\n".join([f"• {s}" for s in steps]) +
        f"\n\n🎯 Продолжайте добавлять шаги или завершите планирование:",
        attachments=[steps_kb()], parse_mode=ParseMode.MARKDOWN
    )


@user_router.message_callback(F.callback.payload == 'end_to_step')
async def end_to_step(call: MessageCallback, context: MemoryContext):
    await call.message.delete()

    data = await context.get_data()
    await context.clear()

    await dbase.new_user(
        call.from_user.user_id,
        data['name'],
        data['email'],
        data['goal'],
        '\n'.join(data['steps'])
    )

    steps_count = len(data['steps'])

    welcome_message = f"""
🎉 **РЕГИСТРАЦИЯ УСПЕШНО ЗАВЕРШЕНА!**

✨ Добро пожаловать в сообщество высокопродуктивных людей, {data['name']}!

📊 **Ваш профиль создан:**

👤 **Имя:** {data['name']}
📧 **Email:** {data['email']}
🎯 **Главная цель:** {data['goal']}
📈 **План действий:** {steps_count} шаг(а/ов)

🚀 **Что дальше?**
Теперь вы готовы начать свой путь к невероятной продуктивности:

• Используйте `/tasks` для работы с задачами
• Настройте умные напоминания через `/reminders`  
• Отслеживайте прогресс в `/stats`
• Получите персональные рекомендации

💫 **Совет на сегодня:**
*"Путь в тысячу миль начинается с первого шага" — и у вас их уже {steps_count}!*

🌟 **Готовы превратить ваши мечты в реальность?**
Вперед — к новым вершинам! 🚀
    """

    await call.message.answer(welcome_message, parse_mode=ParseMode.MARKDOWN, attachments=[steps_kb()])



# @user_router.message_callback(F.callback.payload == 'end_to_step')
# async def end_to_step(call: MessageCallback, context: MemoryContext):
#     await call.message.delete()
#
#     data = await context.get_data()
#     await context.clear()
#
#     dbase.new_user(
#         call.from_user.user_id,
#         data['name'],
#         data['email'],
#         data['goal'],
#         '\n'.join(data['steps'])
#     )
#
#     steps_count = len(data['steps'])
#
#     welcome_message = f"""
# 🎉 **РЕГИСТРАЦИЯ УСПЕШНО ЗАВЕРШЕНА!**
#
# ✨ Добро пожаловать в сообщество высокопродуктивных людей, {data['name']}!
#
# 📊 **Ваш профиль создан:**
#
# 👤 **Имя:** {data['name']}
# 📧 **Email:** {data['email']}
# 🎯 **Главная цель:** {data['goal']}
# 📈 **План действий:** {steps_count} шаг(а/ов)
#
# 🚀 **Что дальше?**
# Теперь вы готовы начать свой путь к невероятной продуктивности:
#
# • Используйте `/tasks` для работы с задачами
# • Настройте умные напоминания через `/reminders`
# • Отслеживайте прогресс в `/stats`
# • Получите персональные рекомендации
#
# 💫 **Совет на сегодня:**
# *"Путь в тысячу миль начинается с первого шага" — и у вас их уже {steps_count}!*
#
# 🌟 **Готовы превратить ваши мечты в реальность?**
# Вперед — к новым вершинам! 🚀
#     """
#
#     await call.message.answer(welcome_message, parse_mode=ParseMode.MARKDOWN)