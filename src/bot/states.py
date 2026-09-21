from aiogram.fsm.state import State, StatesGroup

class Onboarding(StatesGroup):
    language = State()
    name = State()
    gender = State()
    gender_preference = State()
    location = State() # Now covers both city and country via GPS
    origin_region = State()
    willing_to_relocate = State()
    dob_year = State()
    dob_month = State()
    dob_day = State()
    bio = State()
    photos = State()
    confirm = State()
