from maxapi.types import CallbackButton
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder


def steps_kb():
    kb = InlineKeyboardBuilder()
    kb.row(
        CallbackButton(
            text='Закончить шаги',
            payload='end_to_step',
        ),
    )
    return kb.as_markup()