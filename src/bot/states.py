from aiogram.fsm.state import State, StatesGroup

class Onboarding(StatesGroup):
    language = State()
    name = State()
    gender = State()
    gender_preference = State()
    current_country = State()
    current_city = State()
    origin_region = State()
    willing_to_relocate = State()
    dob_year = State()
    dob_month = State()
    dob_day = State()
    bio = State()
    photos = State()
    confirm = State()
