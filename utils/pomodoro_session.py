import asyncio
from datetime import datetime, timedelta
from utils import Dbase


class PomodoroSession:
    def __init__(self, event_id: int, user_id: int):
        self.event_id = event_id
        self.user_id = user_id
        self.work_duration = 25 * 60
        self.break_duration = 5 * 60
        self.long_break_duration = 15 * 60
        self.pomodoros_completed = 0
        self.is_working = False
        self.is_break = False
        self.time_remaining = 0
        self.end_time = None
        self.timer_task = None

    async def load_from_db(self):
        """Загрузить данные из БД"""
        session_data = await Dbase.get_pomodoro_session(self.user_id, self.event_id)
        if session_data:
            self.work_duration = session_data['work_duration']
            self.break_duration = session_data['break_duration']
            self.long_break_duration = session_data['long_break_duration']
            self.pomodoros_completed = session_data['pomodoros_completed']
            self.is_working = bool(session_data['is_working'])
            self.is_break = bool(session_data['is_break'])
            self.time_remaining = session_data['time_remaining']
            self.end_time = session_data['end_time']

    async def save_to_db(self):
        """Сохранить данные в БД"""
        session_data = {
            'user_id': self.user_id,
            'event_id': self.event_id,
            'work_duration': self.work_duration,
            'break_duration': self.break_duration,
            'long_break_duration': self.long_break_duration,
            'pomodoros_completed': self.pomodoros_completed,
            'is_working': self.is_working,
            'is_break': self.is_break,
            'time_remaining': self.time_remaining,
            'end_time': self.end_time
        }
        await Dbase.save_pomodoro_session(session_data)

    async def delete_from_db(self):
        """Удалить сессию из БД"""
        await Dbase.delete_pomodoro_session(self.user_id, self.event_id)

    async def start_work(self):
        """Начать рабочий период"""
        self.is_working = True
        self.is_break = False
        self.time_remaining = self.work_duration
        self.end_time = datetime.now() + timedelta(seconds=self.work_duration)
        await self.save_to_db()

    async def start_break(self):
        """Начать перерыв"""
        self.is_working = False
        self.is_break = True

        if self.pomodoros_completed % 4 == 0:
            self.time_remaining = self.long_break_duration
            self.end_time = datetime.now() + timedelta(seconds=self.long_break_duration)
        else:
            self.time_remaining = self.break_duration
            self.end_time = datetime.now() + timedelta(seconds=self.break_duration)

        await self.save_to_db()

    async def complete_pomodoro(self):
        """Завершить помодоро"""
        self.pomodoros_completed += 1
        await Dbase.update_pomodoro_stats(self.user_id, self.event_id, self.work_duration)
        await self.save_to_db()

    async def pause(self):
        """Приостановить сессию"""
        if self.timer_task and not self.timer_task.done():
            self.timer_task.cancel()

        if self.end_time:
            self.time_remaining = max(0, (self.end_time - datetime.now()).total_seconds())

        await self.save_to_db()

    async def resume(self):
        """Возобновить сессию"""
        if self.time_remaining > 0:
            self.end_time = datetime.now() + timedelta(seconds=self.time_remaining)
            await self.save_to_db()
            return True
        return False

    async def reset_session(self):
        """Полностью сбросить сессию"""
        self.is_working = False
        self.is_break = False
        self.is_paused = False
        self.time_remaining = 0
        self.end_time = None
        self.pomodoros_completed = 0
        await self.save_to_db()