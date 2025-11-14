from maxapi import Router, types, F
from maxapi.context import MemoryContext
from maxapi.enums.parse_mode import ParseMode
from maxapi.types import MessageCreated, MessageCallback

from utils import *

users_routers = Router()


@users_routers.message_callback(F.callback.payload == 'profile')
async def end_to_step(call: MessageCallback):
    await call.message.delete()
    user = await dbase.get_user(call.from_user.user_id)
    await call.message.answer(f"""📊 **Ваш профиль:**

👤 **Имя:** {user[1]}
📧 **Email:** {user[2]}
🎯 **Цель:** {user[3]}
📈 **Шагов выполнено:** {user[4]}
📅 **Дней с нами:** {user[5]}
🔥 **Дней подряд:** {user[6]}

Продолжаем в том же духе! 💪""",
                              parse_mode=ParseMode.MARKDOWN, attachments=[start_kb()])


@users_routers.message_callback(F.callback.payload == 'top')
async def end_to_step(call: MessageCallback):
    await call.message.delete()
    users = await dbase.get_top_users()
    text = "🏆 **Топ самых продуктивных:**\n\n"
    for count, user in enumerate(users):
        text += f"{count + 1}️⃣ {user[0]} - {user[1]} дней\n"

    await call.message.answer(text, parse_mode=ParseMode.MARKDOWN, attachments=[start_kb()])