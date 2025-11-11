from maxapi.types import CallbackButton, RequestGeoLocationButton
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder


def steps_kb():
    kb = InlineKeyboardBuilder()
    kb.row(
        CallbackButton(
            text='✅ Закончить шаги',
            payload='end_to_step',
        ),
    )
    return kb.as_markup()


def start_kb():
    kb = InlineKeyboardBuilder()
    kb.row(CallbackButton(text='👤 Мой профиль', payload='profile'))
    kb.row(CallbackButton(text='🏆 Топ пользователей', payload='top'))
    kb.row(CallbackButton(text='🎯 Мои цели', payload='goals'))
    kb.row(CallbackButton(text='⏱ Pomodoro', payload='pomodoro'))
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