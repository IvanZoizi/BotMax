from maxapi import Router, types, F
from maxapi.context import MemoryContext
from maxapi.types import MessageCreated, MessageCallback

from utils import *

user_router = Router()


@user_router.message_created(RegistrationStates.waiting_for_name)
async def process_name(event: MessageCreated, context: MemoryContext):
    name = event.message.body.text.strip()

    if len(name) < 2:
        await event.message.answer(
            "Имя слишком короткое. Пожалуйста, введите ваше настоящее имя (минимум 2 символа):"
        )
        return

    if len(name) > 50:
        await event.message.answer(
            "Имя слишком длинное. Пожалуйста, введите имя до 50 символов:"
        )
        return

    await context.update_data(name=name)

    await event.message.answer(
        f"Отлично, {name}!\n\n"
        "Теперь введите ваш email адрес. "
        "Мы будем использовать его только для важных уведомлений и восстановления доступа."
    )
    await context.set_state(RegistrationStates.waiting_for_email)


@user_router.message_created(RegistrationStates.waiting_for_email)
async def process_email(event: MessageCreated, context: MemoryContext):
    email = event.message.body.text.strip().lower()

    if "@" not in email or "." not in email or len(email) < 5:
        await event.message.answer(
            "Неверный формат email. Пожалуйста, введите корректный email адрес:\n"
            "example@gmail.com\n"
            "user@mail.ru\n"
            "name@yandex.ru"
        )
        return

    await context.update_data(email=email)

    user_data = await context.get_data()
    name = user_data.get('name', 'друг')

    await event.message.answer(
        f"Прекрасно, {name}!\n\n"
        "Теперь расскажите, какую главную цель вы хотите достичь "
        "с помощью нашего бота?\n\n"
        "Примеры целей:\n"
        "Повысить личную продуктивность на 50%\n"
        "Научиться эффективно планировать свой день\n"
        "Развить 5 полезных привычек за месяц\n"
        "Улучшить концентрацию и фокус внимания\n"
        "Найти баланс между работой и отдыхом\n\n"
        "Опишите своими словами - это поможет нам создать персонализированную программу"
    )
    await context.set_state(RegistrationStates.waiting_for_goal)


@user_router.message_created(RegistrationStates.waiting_for_goal)
async def process_goal(event: MessageCreated, context: MemoryContext):
    goal = event.message.body.text.strip()

    if len(goal) < 10:
        await event.message.answer(
            "Слишком короткое описание цели. Пожалуйста, опишите вашу цель более подробно "
            "(минимум 10 символов). Чем детальнее вы опишете цель, тем лучше мы сможем вам помочь:"
        )
        return

    if len(goal) > 500:
        await event.message.answer(
            "Слишком длинное описание. Пожалуйста, сформулируйте цель более кратко "
            "(максимум 500 символов):"
        )
        return

    await context.update_data(goal=goal, steps=[])

    await event.message.answer(
        "Отличная цель! Теперь давайте разобьем ее на конкретные шаги.\n\n"
        "Добавьте первый шаг к вашей цели:\n\n"
        "Примеры шагов:\n"
        "Составлять план на день каждое утро\n"
        "Читать 15 минут в день по профессиональной литературе\n"
        "Делать 10-минутную зарядку ежедневно\n"
        "Освоить технику Pomodoro для работы\n\n"
        "Добавляйте шаги один за другим - это сделает большую цель достижимой"
    )
    await context.set_state(RegistrationStates.waiting_for_step)


@user_router.message_created(RegistrationStates.waiting_for_step)
async def get_step(event: MessageCreated, context: MemoryContext):
    step = event.message.body.text.strip()

    if len(step) < 5:
        await event.message.answer(
            "Слишком короткое описание шага. Пожалуйста, опишите шаг более подробно (минимум 5 символов). "
            "Конкретный шаг = конкретный результат:"
        )
        return

    data = await context.get_data()
    steps = data['steps']
    steps.append(step)

    current_step_count = len(steps)

    await event.message.answer(
        f"Шаг {current_step_count} добавлен!\n\n"
        f"Текущие шаги ({current_step_count}):\n" +
        "\n".join([f"{s}" for s in steps]) +
        f"\n\nДобавьте еще один шаг или завершите планирование:",
        attachments=[steps_kb()]
    )


@user_router.message_callback(F.callback.payload == 'end_to_step')
async def end_to_step(call: MessageCallback, context: MemoryContext):
    await call.message.delete()

    data = await context.get_data()
    await context.clear()

    dbase.new_user(
        call.from_user.user_id,
        data['name'],
        data['email'],
        data['goal'],
        '\n'.join(data['steps'])
    )

    steps_count = len(data['steps'])

    welcome_message = f"""
Регистрация успешно завершена!

Добро пожаловать в сообщество продуктивных людей, {data['name']}!

Ваш профиль создан:

Имя: {data['name']}
Email: {data['email']}
Главная цель: {data['goal']}
План действий: {steps_count} шаг(а/ов)

Что дальше?
Теперь вы можете начать свой путь к продуктивности:

Используйте /tasks для работы с задачами
Настройте напоминания через /reminders  
Отслеживайте прогресс в /stats
Получите персональные рекомендации

Совет на сегодня:
Путь в тысячу миль начинается с первого шага - и у вас их уже {steps_count}! 

Готовы превратить ваши планы в результаты?
    """

    await call.message.answer(welcome_message)