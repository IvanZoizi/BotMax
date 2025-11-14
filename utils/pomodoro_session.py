


class PomodoroSession:
    def __init__(self, event_id, user_id):
        self.event_id = event_id
        self.user_id = user_id
        self.work_duration = 25 * 60  # 25 минут в секундах
        self.break_duration = 5 * 60  # 5 минут в секундах
        self.long_break_duration = 15 * 60  # 15 минут
        self.pomodoros_completed = 0
        self.is_working = False
        self.is_break = False
        self.time_remaining = 0
        self.timer_task = None