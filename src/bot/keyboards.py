from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from src.bot.locales import get_string

def get_main_menu(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=get_string(lang, "menu_discover"))],
            [KeyboardButton(text=get_string(lang, "menu_matches")),
             KeyboardButton(text=get_string(lang, "menu_profile"))]
        ],
        resize_keyboard=True
    )
