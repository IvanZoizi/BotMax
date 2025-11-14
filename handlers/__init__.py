from .start_user import user_router
from .users import users_routers
from .notification import not_router, scheduler, notification_settings, reminder_notification

routers = [
    user_router,
    users_routers,
    not_router,
]