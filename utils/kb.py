from maxapi.types import CallbackButton, RequestGeoLocationButton
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder

dict_days = {1: 'понедельник', 2: 'вторник', 3: 'среда', 4: 'четверг', 5: 'пятница', 6: 'суббота', 7: 'воскресенье'}


def steps_kb():
    kb = InlineKeyboardBuilder()
    kb.row(
        CallbackButton(
            text='✅ Закончить шаги',
            payload='end_to_step',
        ),
    )
    return kb.as_markup()

def steps_for_update_kb():
    kb = InlineKeyboardBuilder()
    kb.row(
        CallbackButton(
            text='✅ Закончить шаги',
            payload='end_to_step_update',
        ),
    )
    return kb.as_markup()

def start_kb():
    kb = InlineKeyboardBuilder()
    kb.row(CallbackButton(text='👤 Мой профиль', payload='profile'))
    kb.row(CallbackButton(text='🏆 Топ пользователей', payload='top'))
    kb.row(CallbackButton(text='🎯 Изменить цели и шаги', payload='update_goals'))
    kb.row(CallbackButton(text='🔔 Настройка уведомлений', payload='notification'))
    kb.row(CallbackButton(text='⏱ Pomodoro', payload='pomodoro'))
    return kb.as_markup()


def notification_kb():
    kb = InlineKeyboardBuilder()
    kb.row(CallbackButton(text='📋 Мои уведомления', payload='my_notification_0'))
    kb.row(CallbackButton(text='➕ Создать уведомление', payload='new_notification'))
    kb.row(CallbackButton(text='🔙 Назад', payload='start'))
    return kb.as_markup()

def make_mail_user_kb(text):
    kb = InlineKeyboardBuilder()
    kb.row(CallbackButton(text=text, payload='pomodoro'))
    return kb.as_markup()

def my_notification_kb(data, num):

    kb = InlineKeyboardBuilder()

    new_data = data[num * 8:(num + 1) * 8]

    for i in new_data:
        kb.row(CallbackButton(text=f"{dict_days[i[2]][:3]} - {i[3]}", payload=f"get_notification_{i[0]}"))

    kb_data = []
    if num == 1:
        kb_data.append(CallbackButton(text=f"◀️ Предыдущее", payload=f"my_notification_{num - 1}"))
    if (num + 1) * 8 < len(data):
        kb_data.append(CallbackButton(text=f"Далее ▶️", payload=f"my_notification_{num + 1}"))


    if kb_data:
        kb.row(*kb_data)
    kb.row(CallbackButton(text='🔙 Назад', payload='notification'))

    return kb.as_markup()


def get_notification_kb(id):

    kb = InlineKeyboardBuilder()

    kb.row(CallbackButton(text="🗑️ Удалить уведомление", payload=f'delete_notification_{id}'))
    kb.row(CallbackButton(text="✏️ Изменить время", payload=f'update_notification_{id}'))
    kb.row(CallbackButton(text='🔙 Назад', payload='my_notification_0'))

    return kb.as_markup()


def set_days_kb(days):

    matrix = [
        ["понедельник", 1],
        ["вторник", 2],
        ["среда", 3],
        ["четверг", 4],
        ["пятница", 5],
        ["суббота", 6],
        ["воскресенье", 7]
    ]

    kb = InlineKeyboardBuilder()
    for i in matrix:
        if i[1] in days:
            kb.row(CallbackButton(text=f"{i[0].capitalize()} ✅", payload=f"set_day_{i[1]}"))
        else:
            kb.row(CallbackButton(text=f"{i[0].capitalize()} ❌", payload=f"set_day_{i[1]}"))

    kb.row(CallbackButton(text='✅ Подтвердить', payload='accept_days'),
           CallbackButton(text='🔙 Назад', payload='notification'))

    return kb.as_markup()


def location_kb():
    kb = InlineKeyboardBuilder()
    kb.row(RequestGeoLocationButton(text="📍 Отправить геолокацию"))
    kb.row(CallbackButton(text='🚫 Пропустить', payload="dont_geo"))
    return kb.as_markup()


def goals_kb():
    kb = InlineKeyboardBuilder()
    kb.row(CallbackButton(text='➕ Новая цель', payload='add_goal'))
    kb.row(CallbackButton(text='📋 Мои цели', payload='my_goals'))
    kb.row(CallbackButton(text='📊 Прогресс', payload='progress'))
    kb.row(CallbackButton(text='🔙 Назад', payload='back'))
    return kb.as_markup()


def pomodoro_kb():
    kb = InlineKeyboardBuilder()
    kb.row(CallbackButton(text='▶️ Старт 25 мин', payload='pomodoro_start'))
    kb.row(CallbackButton(text='⏸ Пауза', payload='pomodoro_pause'))
    kb.row(CallbackButton(text='⏹ Стоп', payload='pomodoro_stop'))
    kb.row(CallbackButton(text='🔙 Назад', payload='back'))
    return kb.as_markup()


def habits_kb():
    kb = InlineKeyboardBuilder()
    kb.row(CallbackButton(text='💪 Добавить привычку', payload='add_habit'))
    kb.row(CallbackButton(text='📈 Отслеживать', payload='track_habit'))
    kb.row(CallbackButton(text='📊 Статистика', payload='habits_stats'))
    kb.row(CallbackButton(text='🔙 Назад', payload='back'))
    return kb.as_markup()


def back_kb():
    kb = InlineKeyboardBuilder()
    kb.row(CallbackButton(text='🔙 Назад', payload='back'))
    return kb.as_markup()


def confirm_kb():
    kb = InlineKeyboardBuilder()
    kb.row(CallbackButton(text='✅ Подтвердить', payload='confirm'))
    kb.row(CallbackButton(text='❌ Отмена', payload='cancel'))
    return kb.as_markup()