from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from src.bot.states import Onboarding
from src.bot.locales import get_string
from src.database.session import async_session_maker
from src.database.models import User, Photo
from datetime import date
import re

router = Router(name="onboarding")

def get_lang(data: dict) -> str:
    return data.get("lang", "en")

def get_main_menu(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=get_string(lang, "menu_discover"))],
            [KeyboardButton(text=get_string(lang, "menu_matches")),
             KeyboardButton(text=get_string(lang, "menu_profile"))]
        ],
        resize_keyboard=True
    )

def calculate_age(dob: date) -> int:
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    async with async_session_maker() as session:
        user = await session.get(User, message.from_user.id)
        if user:
            await message.answer("You already have an account!", reply_markup=get_main_menu(user.language_pref))
            return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="English 🇺🇸", callback_data="lang_en"),
         InlineKeyboardButton(text="አማርኛ 🇪🇹", callback_data="lang_am")]
    ])
    await message.answer(get_string("en", "welcome"), reply_markup=kb)
    await state.set_state(Onboarding.language)

@router.callback_query(Onboarding.language, F.data.startswith("lang_"))
async def process_language(callback: CallbackQuery, state: FSMContext):
    lang = callback.data.split("_")[1]
    await state.update_data(lang=lang)
    await callback.message.edit_reply_markup(reply_markup=None)
    
    await callback.message.answer(get_string(lang, "ask_name"))
    await state.set_state(Onboarding.name)
    await callback.answer()

async def prompt_dob_year(message_target, lang: str, state: FSMContext):
    current_year = date.today().year
    years = list(range(current_year - 50, current_year - 17)) # 18 to 50 years old
    
    keyboard = []
    row = []
    for y in years:
        row.append(InlineKeyboardButton(text=str(y), callback_data=f"year_{y}"))
        if len(row) == 5:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
        
    kb = InlineKeyboardMarkup(inline_keyboard=keyboard)
    await message_target.answer(get_string(lang, "ask_dob_year"), reply_markup=kb)
    await state.set_state(Onboarding.dob_year)

@router.message(Onboarding.name, F.text)
async def process_name(message: Message, state: FSMContext):
    lang = get_lang(await state.get_data())
    await state.update_data(name=message.text)
    await prompt_dob_year(message, lang, state)

@router.callback_query(Onboarding.dob_year, F.data.startswith("year_"))
async def process_dob_year(callback: CallbackQuery, state: FSMContext):
    lang = get_lang(await state.get_data())
    year = int(callback.data.split("_")[1])
    await state.update_data(dob_year=year)
    await callback.message.edit_reply_markup(reply_markup=None)
    
    keyboard = []
    row = []
    for m in range(1, 13):
        row.append(InlineKeyboardButton(text=str(m), callback_data=f"month_{m}"))
        if len(row) == 4:
            keyboard.append(row)
            row = []
            
    kb = InlineKeyboardMarkup(inline_keyboard=keyboard)
    await callback.message.answer(get_string(lang, "ask_dob_month"), reply_markup=kb)
    await state.set_state(Onboarding.dob_month)
    await callback.answer()

@router.callback_query(Onboarding.dob_month, F.data.startswith("month_"))
async def process_dob_month(callback: CallbackQuery, state: FSMContext):
    lang = get_lang(await state.get_data())
    month = int(callback.data.split("_")[1])
    await state.update_data(dob_month=month)
    await callback.message.edit_reply_markup(reply_markup=None)
    
    keyboard = []
    row = []
    for d in range(1, 32):
        row.append(InlineKeyboardButton(text=str(d), callback_data=f"day_{d}"))
        if len(row) == 7:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
            
    kb = InlineKeyboardMarkup(inline_keyboard=keyboard)
    await callback.message.answer(get_string(lang, "ask_dob_day"), reply_markup=kb)
    await state.set_state(Onboarding.dob_day)
    await callback.answer()

@router.callback_query(Onboarding.dob_day, F.data.startswith("day_"))
async def process_dob_day(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = get_lang(data)
    day = int(callback.data.split("_")[1])
    year = data["dob_year"]
    month = data["dob_month"]
    
    try:
        dob = date(year, month, day)
    except ValueError:
        # Invalid date (e.g. Feb 30)
        await callback.answer("Invalid date, please select again.", show_alert=True)
        # Resend day picker
        return
        
    await state.update_data(dob_day=day, dob_str=dob.strftime("%Y-%m-%d"), age=calculate_age(dob))
    await callback.message.edit_reply_markup(reply_markup=None)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_string(lang, "btn_male"), callback_data="gender_male"),
         InlineKeyboardButton(text=get_string(lang, "btn_female"), callback_data="gender_female")]
    ])
    await callback.message.answer(get_string(lang, "ask_gender"), reply_markup=kb)
    await state.set_state(Onboarding.gender)
    await callback.answer()

@router.callback_query(Onboarding.gender, F.data.startswith("gender_"))
async def process_gender(callback: CallbackQuery, state: FSMContext):
    lang = get_lang(await state.get_data())
    gender = callback.data.split("_")[1]
    await state.update_data(gender=gender)
    await callback.message.edit_reply_markup(reply_markup=None)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_string(lang, "btn_male"), callback_data="pref_male"),
         InlineKeyboardButton(text=get_string(lang, "btn_female"), callback_data="pref_female")]
    ])
    await callback.message.answer(get_string(lang, "ask_gender_pref"), reply_markup=kb)
    await state.set_state(Onboarding.gender_preference)
    await callback.answer()

async def prompt_country(message_target, lang: str, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_string(lang, "btn_ethiopia"), callback_data="country_Ethiopia"),
         InlineKeyboardButton(text=get_string(lang, "btn_usa"), callback_data="country_USA")],
        [InlineKeyboardButton(text=get_string(lang, "btn_canada"), callback_data="country_Canada"),
         InlineKeyboardButton(text=get_string(lang, "btn_europe"), callback_data="country_Europe")],
        [InlineKeyboardButton(text=get_string(lang, "btn_uae"), callback_data="country_UAE"),
         InlineKeyboardButton(text=get_string(lang, "btn_other"), callback_data="country_Other")]
    ])
    await message_target.answer(get_string(lang, "ask_country"), reply_markup=kb)
    await state.set_state(Onboarding.current_country)

@router.callback_query(Onboarding.gender_preference, F.data.startswith("pref_"))
async def process_gender_pref(callback: CallbackQuery, state: FSMContext):
    lang = get_lang(await state.get_data())
    pref = callback.data.split("_")[1]
    await state.update_data(gender_preference=pref)
    await callback.message.edit_reply_markup(reply_markup=None)
    
    await prompt_country(callback.message, lang, state)
    await callback.answer()

async def prompt_city(message_target, lang: str, country: str, state: FSMContext):
    if country == "Ethiopia":
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_string(lang, "btn_addis"), callback_data="city_Addis_Ababa"),
             InlineKeyboardButton(text=get_string(lang, "btn_adama"), callback_data="city_Adama")],
            [InlineKeyboardButton(text=get_string(lang, "btn_hawassa"), callback_data="city_Hawassa"),
             InlineKeyboardButton(text=get_string(lang, "btn_bahirdar"), callback_data="city_Bahir_Dar")],
            [InlineKeyboardButton(text=get_string(lang, "btn_dire"), callback_data="city_Dire_Dawa"),
             InlineKeyboardButton(text=get_string(lang, "btn_mekelle"), callback_data="city_Mekelle")],
            [InlineKeyboardButton(text=get_string(lang, "btn_other"), callback_data="city_Other")]
        ])
        await message_target.answer(get_string(lang, "ask_city"), reply_markup=kb)
        await state.set_state(Onboarding.current_city)
    else:
        await message_target.answer(get_string(lang, "ask_city"))
        await state.set_state(Onboarding.current_city)

@router.callback_query(Onboarding.current_country, F.data.startswith("country_"))
async def process_country_cb(callback: CallbackQuery, state: FSMContext):
    lang = get_lang(await state.get_data())
    country = callback.data.split("_")[1]
    await callback.message.edit_reply_markup(reply_markup=None)
    
    if country == "Other":
        await callback.message.answer(get_string(lang, "ask_country"))
        return
        
    await state.update_data(current_country=country)
    await prompt_city(callback.message, lang, country, state)
    await callback.answer()

@router.message(Onboarding.current_country, F.text)
async def process_country_text(message: Message, state: FSMContext):
    lang = get_lang(await state.get_data())
    await state.update_data(current_country=message.text)
    await prompt_city(message, lang, message.text, state)

async def prompt_origin(message_target, lang: str, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_string(lang, "btn_addis"), callback_data="origin_Addis_Ababa"),
         InlineKeyboardButton(text=get_string(lang, "btn_oromia"), callback_data="origin_Oromia")],
        [InlineKeyboardButton(text=get_string(lang, "btn_amhara"), callback_data="origin_Amhara"),
         InlineKeyboardButton(text=get_string(lang, "btn_tigray"), callback_data="origin_Tigray")],
        [InlineKeyboardButton(text=get_string(lang, "btn_sidama"), callback_data="origin_Sidama"),
         InlineKeyboardButton(text=get_string(lang, "btn_snnpr"), callback_data="origin_SNNPR")],
        [InlineKeyboardButton(text=get_string(lang, "btn_other"), callback_data="origin_Other")]
    ])
    await message_target.answer(get_string(lang, "ask_origin"), reply_markup=kb)
    await state.set_state(Onboarding.origin_region)

@router.callback_query(Onboarding.current_city, F.data.startswith("city_"))
async def process_city_cb(callback: CallbackQuery, state: FSMContext):
    lang = get_lang(await state.get_data())
    city = callback.data.split("_", 1)[1].replace("_", " ")
    await callback.message.edit_reply_markup(reply_markup=None)
    
    if city == "Other":
        await callback.message.answer(get_string(lang, "ask_city"))
        return
        
    await state.update_data(current_city=city)
    await prompt_origin(callback.message, lang, state)
    await callback.answer()

@router.message(Onboarding.current_city, F.text)
async def process_city_text(message: Message, state: FSMContext):
    lang = get_lang(await state.get_data())
    await state.update_data(current_city=message.text)
    await prompt_origin(message, lang, state)

async def prompt_relocate(message_target, lang: str, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_string(lang, "btn_yes"), callback_data="relocate_yes"),
         InlineKeyboardButton(text=get_string(lang, "btn_no"), callback_data="relocate_no")]
    ])
    await message_target.answer(get_string(lang, "ask_relocate"), reply_markup=kb)
    await state.set_state(Onboarding.willing_to_relocate)

@router.callback_query(Onboarding.origin_region, F.data.startswith("origin_"))
async def process_origin_cb(callback: CallbackQuery, state: FSMContext):
    lang = get_lang(await state.get_data())
    origin = callback.data.split("_", 1)[1].replace("_", " ")
    await callback.message.edit_reply_markup(reply_markup=None)
    
    if origin == "Other":
        await callback.message.answer(get_string(lang, "ask_origin"))
        return
        
    await state.update_data(origin_region=origin)
    await prompt_relocate(callback.message, lang, state)
    await callback.answer()

@router.message(Onboarding.origin_region, F.text)
async def process_origin_text(message: Message, state: FSMContext):
    lang = get_lang(await state.get_data())
    await state.update_data(origin_region=message.text)
    await prompt_relocate(message, lang, state)

@router.callback_query(Onboarding.willing_to_relocate, F.data.startswith("relocate_"))
async def process_relocate_cb(callback: CallbackQuery, state: FSMContext):
    lang = get_lang(await state.get_data())
    will = callback.data.split("_")[1] == "yes"
    await state.update_data(willing_to_relocate=will)
    await callback.message.edit_reply_markup(reply_markup=None)
    
    await callback.message.answer(get_string(lang, "ask_bio"))
    await state.set_state(Onboarding.bio)
    await callback.answer()

@router.message(Onboarding.bio, F.text)
async def process_bio(message: Message, state: FSMContext):
    lang = get_lang(await state.get_data())
    await state.update_data(bio=message.text)
    await state.update_data(photos=[])
    await message.answer(get_string(lang, "ask_photos"))
    await state.set_state(Onboarding.photos)

@router.message(Onboarding.photos, F.photo)
async def process_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])
    file_id = message.photo[-1].file_id
    photos.append(file_id)
    await state.update_data(photos=photos)

@router.message(Onboarding.photos, Command("done"))
async def process_photos_done(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = get_lang(data)
    
    if len(data.get("photos", [])) < 2:
        await message.answer(get_string(lang, "ask_photos"))
        return
        
    async with async_session_maker() as session:
        user = await session.get(User, message.from_user.id)
        if not user:
            user = User(telegram_id=message.from_user.id)
            session.add(user)
            
        user.telegram_username = message.from_user.username
        user.name = data["name"]
        user.age = data["age"]
        user.gender = data["gender"]
        user.gender_preference = data["gender_preference"]
        user.current_country = data["current_country"]
        user.current_city = data["current_city"]
        user.origin_region = data["origin_region"]
        user.willing_to_relocate = data["willing_to_relocate"]
        user.bio = data["bio"]
        user.date_of_birth = data["dob_str"]
        user.language_pref = lang

        # Delete old photos
        await session.execute(
            Photo.__table__.delete().where(Photo.user_id == message.from_user.id)
        )
        
        for i, file_id in enumerate(data["photos"]):
            photo = Photo(
                user_id=message.from_user.id,
                telegram_file_id=file_id,
                sort_order=i,
                is_primary=(i == 0)
            )
            session.add(photo)
        await session.commit()
        
    await message.answer(get_string(lang, "profile_saved"), reply_markup=get_main_menu(lang))
    await state.clear()
