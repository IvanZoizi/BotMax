from .pomodoro import pomodoro_router
from .start_user import user_router
from .users import users_routers

routers = [
    user_router,
    users_routers,
    pomodoro_router
]