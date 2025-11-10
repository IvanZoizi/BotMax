from maxapi.context import StatesGroup, State

class RegistrationStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_email = State()
    waiting_for_goal = State()
    waiting_for_step = State()