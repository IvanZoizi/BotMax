from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import datetime

user_router = Router()


def get_registration_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Зарегистрироваться")],
            [KeyboardButton(text="ℹ️ О боте")]
        ],
        resize_keyboard=True
    )


# Клавиатура для отмены
def get_cancel_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Отменить регистрацию")]
        ],
        resize_keyboard=True
    )


@user_router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    welcome_text = """
🤖 Добро пожаловать в бот продуктивности "Фокус"!

Здесь вы сможете:
• Ставить цели и задачи
• Использовать технику Pomodoro
• Отслеживать привычки
• Получать персональные рекомендации

Для начала работы необходимо зарегистрироваться!
    """

    await message.answer(welcome_text, reply_markup=get_registration_keyboard())


@router.message(F.text == "📝 Зарегистрироваться")
async def start_registration(message: Message, state: FSMContext):
    """Начало процесса регистрации"""
    user_id = message.from_user.id

    # Проверяем, не зарегистрирован ли уже пользователь
    if user_id in user_data.users:
        await message.answer(
            "✅ Вы уже зарегистрированы!\n"
            "Используйте /profile для просмотра данных",
            reply_markup=get_registration_keyboard()
        )
        return

    await message.answer(
        "📝 Начинаем регистрацию!\n\n"
        "Пожалуйста, введите ваше имя:",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(RegistrationStates.waiting_for_name)


@router.message(F.text == "❌ Отменить регистрацию")
async def cancel_registration(message: Message, state: FSMContext):
    """Отмена регистрации"""
    await state.clear()
    await message.answer(
        "❌ Регистрация отменена.",
        reply_markup=get_registration_keyboard()
    )


@router.message(RegistrationStates.waiting_for_name, F.text)
async def process_name(message: Message, state: FSMContext):
    """Обработка имени пользователя"""
    name = message.text.strip()

    if len(name) < 2:
        await message.answer("❌ Имя должно содержать минимум 2 символа. Попробуйте еще раз:")
        return

    # Сохраняем имя в состоянии
    await state.update_data(name=name)

    await message.answer(
        f"👋 Отлично, {name}!\n\n"
        "Теперь введите ваш email:",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(RegistrationStates.waiting_for_email)


@router.message(RegistrationStates.waiting_for_email, F.text)
async def process_email(message: Message, state: FSMContext):
    """Обработка email пользователя"""
    email = message.text.strip()

    # Простая валидация email
    if "@" not in email or "." not in email:
        await message.answer("❌ Пожалуйста, введите корректный email адрес:")
        return

    await state.update_data(email=email)

    await message.answer(
        "🎯 Прекрасно!\n\n"
        "Теперь расскажите, какую цель вы хотите достичь "
        "с помощью этого бота?\n"
        "Например: 'повысить продуктивность', 'следить за привычками', "
        "'лучше планировать время'",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(RegistrationStates.waiting_for_goal)


@router.message(RegistrationStates.waiting_for_goal, F.text)
async def process_goal(message: Message, state: FSMContext):
    """Обработка цели пользователя и завершение регистрации"""
    goal = message.text.strip()

    if len(goal) < 5:
        await message.answer("❌ Пожалуйста, опишите цель подробнее (минимум 5 символов):")
        return

    # Получаем все данные из состояния
    data = await state.get_data()

    # Создаем запись пользователя
    user_id = message.from_user.id
    user_info = {
        "user_id": user_id,
        "username": message.from_user.username,
        "first_name": message.from_user.first_name,
        "last_name": message.from_user.last_name,
        "name": data['name'],
        "email": data['email'],
        "goal": goal,
        "registration_date": datetime.datetime.now().isoformat(),
        "timezone": "UTC+3"  # Можно добавить выбор часового пояса
    }

    # Сохраняем пользователя (пока в памяти)
    user_data.users[user_id] = user_info

    # Выводим данные в консоль
    print("\n" + "=" * 50)
    print("🎉 НОВЫЙ ПОЛЬЗОВАТЕЛЬ ЗАРЕГИСТРИРОВАН!")
    print("=" * 50)
    print(f"ID: {user_info['user_id']}")
    print(f"Username: @{user_info['username']}")
    print(f"Имя в Telegram: {user_info['first_name']} {user_info['last_name'] or ''}")
    print(f"Имя при регистрации: {user_info['name']}")
    print(f"Email: {user_info['email']}")
    print(f"Цель: {user_info['goal']}")
    print(f"Дата регистрации: {user_info['registration_date']}")
    print("=" * 50 + "\n")

    # Завершаем состояние
    await state.clear()

    # Отправляем приветственное сообщение
    welcome_message = f"""
✅ Регистрация завершена, {data['name']}!

📋 Ваши данные:
• Имя: {data['name']}
• Email: {data['email']}
• Цель: {goal}

Теперь вы можете использовать все возможности бота:
• /tasks - управление задачами
• /pomodoro - техника Pomodoro
• /habits - трекер привычек
• /profile - ваш профиль

Желаю продуктивного дня! 🚀
    """

    await message.answer(welcome_message, reply_markup=get_registration_keyboard())


@router.message(Command("profile"))
async def cmd_profile(message: Message):
    """Просмотр профиля пользователя"""
    user_id = message.from_user.id

    if user_id not in user_data.users:
        await message.answer(
            "❌ Вы еще не зарегистрированы.\n"
            "Нажмите '📝 Зарегистрироваться' чтобы начать!",
            reply_markup=get_registration_keyboard()
        )
        return

    user_info = user_data.users[user_id]

    profile_text = f"""
👤 Ваш профиль:

📝 Имя: {user_info['name']}
📧 Email: {user_info['email']}
🎯 Цель: {user_info['goal']}
📅 Зарегистрирован: {user_info['registration_date'][:10]}
🌐 Часовой пояс: {user_info['timezone']}

Используйте /help для списка команд
    """

    await message.answer(profile_text)


@router.message(Command("users"))
async def cmd_users(message: Message):
    """Команда для просмотра всех пользователей (для отладки)"""
    if not user_data.users:
        await message.answer("📭 Пользователей пока нет")
        return

    users_list = "📊 Зарегистрированные пользователи:\n\n"
    for user_id, user_info in user_data.users.items():
        users_list += f"• {user_info['name']} (@{user_info['username']}) - {user_info['goal']}\n"

    await message.answer(users_list)


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Справка по командам"""
    help_text = """
📋 Доступные команды:

/start - начать работу с ботом
/profile - просмотреть свой профиль
/tasks - управление задачами (скоро)
/pomodoro - техника Pomodoro (скоро)
/habits - трекер привычек (скоро)
/users - список пользователей (отладка)

📝 Для регистрации используйте кнопку "Зарегистрироваться"
    """
    await message.answer(help_text)


@router.message(F.text == "ℹ️ О боте")
async def about_bot(message: Message):
    """Информация о боте"""
    about_text = """
🤖 Бот продуктивности "Фокус"

Этот бот поможет вам:
• Ставить и достигать цели
• Эффективно планировать время
• Развивать полезные привычки
• Повышать личную продуктивность

Используйте меню для навигации!
    """
    await message.answer(about_text)