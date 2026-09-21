from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from sqlalchemy import select

from src.database.session import async_session_maker
from src.database.models import User, Photo
from src.bot.states import Onboarding
from src.bot.keyboards import get_main_menu
from src.bot.locales import get_string
from src.utils.geocoding import reverse_geocode
import datetime

router = Router()

def get_lang(data: dict) -> str:
    return data.get("lang", "en")

def get_skip_kb(lang: str, current_val: str, callback_data: str) -> InlineKeyboardMarkup:
    """Returns a keyboard with a single Skip button showing the current value."""
    # Truncate if too long
    if len(current_val) > 20:
        current_val = current_val[:17] + "..."
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"⏭️ Skip (Keep: {current_val})", callback_data=callback_data)]
    ])

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    async with async_session_maker() as session:
        user = await session.get(User, message.from_user.id)
        if user:
            lang = user.language_pref
            await message.answer(
                f"Welcome back, {user.name}! 🌟\nUse the menu below to navigate.", 
                reply_markup=get_main_menu(lang)
            )
            return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="English 🇬🇧", callback_data="lang_en"),
         InlineKeyboardButton(text="አማርኛ 🇪🇹", callback_data="lang_am")]
    ])
    await message.answer(get_string("en", "welcome"), reply_markup=kb)
    await state.set_state(Onboarding.language)

@router.callback_query(Onboarding.language, F.data.startswith("lang_"))
async def process_language(callback: CallbackQuery, state: FSMContext):
    lang = callback.data.split("_")[1]
    await state.update_data(lang=lang)
    await callback.message.edit_reply_markup(reply_markup=None)
    
    data = await state.get_data()
    kb = None
    if "name" in data:
        kb = get_skip_kb(lang, data["name"], "skip_name")
        
    await callback.message.answer(get_string(lang, "ask_name"), reply_markup=kb)
    await state.set_state(Onboarding.name)
    await callback.answer()

@router.callback_query(Onboarding.name, F.data == "skip_name")
async def skip_name(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    data = await state.get_data()
    lang = get_lang(data)
    await prompt_dob_year(callback.message, lang, data)
    await callback.answer()

@router.message(Onboarding.name, F.text)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    data = await state.get_data()
    lang = get_lang(data)
    await prompt_dob_year(message, lang, data)

async def prompt_dob_year(message, lang, data):
    kb_buttons = []
    if "dob_str" in data:
        kb_buttons.append([InlineKeyboardButton(text=f"⏭️ Skip (Keep: {data['dob_str']})", callback_data="skip_dob")])
        
    # Generate decades/years (e.g. 1980-2005)
    current_year = datetime.datetime.now().year
    years = list(range(current_year - 18, current_year - 60, -1))
    
    # We will just show a few options or let them type it for simplicity.
    # To keep it simple, we ask them to type their birth year.
    if kb_buttons:
        kb = InlineKeyboardMarkup(inline_keyboard=kb_buttons)
        await message.answer(get_string(lang, "ask_dob_year"), reply_markup=kb)
    else:
        await message.answer(get_string(lang, "ask_dob_year"))
    from src.bot.states import Onboarding
    import builtins
    if not isinstance(message, Message): # If called from callback, message is Message object.
        # It's always a message object here because we pass callback.message or message
        pass
    
    # Wait, the original flow used inline calendars.
    # Let's retain the calendar logic.
    year_rows = []
    for i in range(0, min(12, len(years)), 4):
        row = [InlineKeyboardButton(text=str(y), callback_data=f"dobyear_{y}") for y in years[i:i+4]]
        year_rows.append(row)
    
    kb = InlineKeyboardMarkup(inline_keyboard=year_rows + kb_buttons)
    await message.answer(get_string(lang, "ask_dob_year"), reply_markup=kb)
    from src.bot.states import Onboarding
    await state.set_state(Onboarding.dob_year)

@router.callback_query(Onboarding.dob_year, F.data == "skip_dob")
async def skip_dob(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    data = await state.get_data()
    lang = get_lang(data)
    await prompt_gender(callback.message, lang, data)
    await callback.answer()

@router.callback_query(Onboarding.dob_year, F.data.startswith("dobyear_"))
async def process_dob_year(callback: CallbackQuery, state: FSMContext):
    year = int(callback.data.split("_")[1])
    await state.update_data(dob_year=year)
    await callback.message.edit_reply_markup(reply_markup=None)
    
    lang = get_lang(await state.get_data())
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    m_rows = []
    for i in range(0, 12, 4):
        row = [InlineKeyboardButton(text=m, callback_data=f"dobmonth_{i+j+1}") for j, m in enumerate(months[i:i+4])]
        m_rows.append(row)
        
    kb = InlineKeyboardMarkup(inline_keyboard=m_rows)
    await callback.message.answer(get_string(lang, "ask_dob_month"), reply_markup=kb)
    await state.set_state(Onboarding.dob_month)
    await callback.answer()

@router.callback_query(Onboarding.dob_month, F.data.startswith("dobmonth_"))
async def process_dob_month(callback: CallbackQuery, state: FSMContext):
    month = int(callback.data.split("_")[1])
    await state.update_data(dob_month=month)
    await callback.message.edit_reply_markup(reply_markup=None)
    
    lang = get_lang(await state.get_data())
    d_rows = []
    for i in range(1, 32, 7):
        row = [InlineKeyboardButton(text=str(d), callback_data=f"dobday_{d}") for d in range(i, min(i+7, 32))]
        d_rows.append(row)
        
    kb = InlineKeyboardMarkup(inline_keyboard=d_rows)
    await callback.message.answer(get_string(lang, "ask_dob_day"), reply_markup=kb)
    await state.set_state(Onboarding.dob_day)
    await callback.answer()

@router.callback_query(Onboarding.dob_day, F.data.startswith("dobday_"))
async def process_dob_day(callback: CallbackQuery, state: FSMContext):
    day = int(callback.data.split("_")[1])
    data = await state.get_data()
    year = data["dob_year"]
    month = data["dob_month"]
    
    try:
        dob = datetime.date(year, month, day)
    except ValueError:
        await callback.answer("Invalid date, try again.", show_alert=True)
        return
        
    today = datetime.date.today()
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    
    if age < 18:
        await callback.answer("You must be at least 18 years old to use this bot.", show_alert=True)
        return
        
    await state.update_data(dob_str=dob.isoformat(), age=age)
    await callback.message.edit_reply_markup(reply_markup=None)
    
    data = await state.get_data()
    lang = get_lang(data)
    await prompt_gender(callback.message, lang, data)
    await callback.answer()

async def prompt_gender(message, lang, data):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    from src.bot.locales import get_string
    
    kb_buttons = [
        [InlineKeyboardButton(text=get_string(lang, "btn_male"), callback_data="gender_Male"),
         InlineKeyboardButton(text=get_string(lang, "btn_female"), callback_data="gender_Female")]
    ]
    if "gender" in data:
        kb_buttons.append([InlineKeyboardButton(text=f"⏭️ Skip (Keep: {data['gender']})", callback_data="skip_gender")])
        
    kb = InlineKeyboardMarkup(inline_keyboard=kb_buttons)
    await message.answer(get_string(lang, "ask_gender"), reply_markup=kb)
    from src.bot.states import Onboarding
    import aiogram
    # Setting state needs context. We will set it outside.

@router.callback_query(Onboarding.dob_day)
async def fallback_dob(callback: CallbackQuery, state: FSMContext):
    from src.bot.states import Onboarding
    await state.set_state(Onboarding.gender)

@router.callback_query(Onboarding.gender, F.data == "skip_gender")
async def skip_gender(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    data = await state.get_data()
    lang = get_lang(data)
    await prompt_gender_pref(callback.message, lang, data)
    await callback.answer()

@router.callback_query(Onboarding.gender, F.data.startswith("gender_"))
async def process_gender(callback: CallbackQuery, state: FSMContext):
    lang = get_lang(await state.get_data())
    gender = callback.data.split("_")[1]
    await state.update_data(gender=gender)
    await callback.message.edit_reply_markup(reply_markup=None)
    
    data = await state.get_data()
    await prompt_gender_pref(callback.message, lang, data)
    await callback.answer()

async def prompt_gender_pref(message, lang, data):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    from src.bot.locales import get_string
    
    kb_buttons = [
        [InlineKeyboardButton(text=get_string(lang, "btn_male"), callback_data="pref_male"),
         InlineKeyboardButton(text=get_string(lang, "btn_female"), callback_data="pref_female")]
    ]
    if "gender_preference" in data:
        kb_buttons.append([InlineKeyboardButton(text=f"⏭️ Skip (Keep: {data['gender_preference']})", callback_data="skip_pref")])
        
    kb = InlineKeyboardMarkup(inline_keyboard=kb_buttons)
    await message.answer(get_string(lang, "ask_gender_pref"), reply_markup=kb)
    from src.bot.states import Onboarding
    # The caller sets the state

@router.callback_query(Onboarding.gender)
async def fallback_gender(callback: CallbackQuery, state: FSMContext):
    from src.bot.states import Onboarding
    await state.set_state(Onboarding.gender_preference)

@router.callback_query(Onboarding.gender_preference, F.data == "skip_pref")
async def skip_pref(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    data = await state.get_data()
    lang = get_lang(data)
    await prompt_location(callback.message, lang, data)
    await callback.answer()

@router.callback_query(Onboarding.gender_preference, F.data.startswith("pref_"))
async def process_gender_pref(callback: CallbackQuery, state: FSMContext):
    lang = get_lang(await state.get_data())
    pref = callback.data.split("_")[1]
    await state.update_data(gender_preference=pref)
    await callback.message.edit_reply_markup(reply_markup=None)
    
    data = await state.get_data()
    await prompt_location(callback.message, lang, data)
    await callback.answer()

async def prompt_location(message, lang, data):
    from src.bot.states import Onboarding
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📍 Share Location", request_location=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    text = "Where do you live? Please tap 'Share Location' to grab your exact city, or type your city name manually."
    if lang == "am":
        text = "የሚኖሩበትን ቦታ ያጋሩ? እባክዎ 'Share Location' የሚለውን ይጫኑ ወይም ከተማዎን ይፃፉ።"
        
    if "current_city" in data:
        text += f"\n\n(Current: {data['current_city']}. Type 'skip' to keep it.)"
        
    await message.answer(text, reply_markup=kb)
    # the caller will set the state to location

@router.callback_query(Onboarding.gender_preference)
async def fallback_gender_pref(callback: CallbackQuery, state: FSMContext):
    from src.bot.states import Onboarding
    await state.set_state(Onboarding.location)

@router.message(Onboarding.location, F.location)
async def process_location_gps(message: Message, state: FSMContext):
    lat = message.location.latitude
    lon = message.location.longitude
    
    await message.answer("📍 Fetching your city... (እየፈለግን ነው...)", reply_markup=ReplyKeyboardRemove())
    city, country = await reverse_geocode(lat, lon)
    
    await state.update_data(latitude=lat, longitude=lon, current_city=city, current_country=country)
    
    data = await state.get_data()
    lang = get_lang(data)
    await message.answer(f"✅ Location set to: {city}, {country}")
    await prompt_origin(message, lang, data)

@router.message(Onboarding.location, F.text)
async def process_location_text(message: Message, state: FSMContext):
    text = message.text.strip().lower()
    data = await state.get_data()
    lang = get_lang(data)
    
    if text == "skip" and "current_city" in data:
        await message.answer("⏭️ Skipped.", reply_markup=ReplyKeyboardRemove())
        await prompt_origin(message, lang, data)
        return
        
    await state.update_data(current_city=message.text, current_country="Ethiopia", latitude=None, longitude=None)
    await message.answer(f"✅ Location set manually.", reply_markup=ReplyKeyboardRemove())
    await prompt_origin(message, lang, data)

async def prompt_origin(message, lang, data):
    from src.bot.states import Onboarding
    kb_buttons = [
        [InlineKeyboardButton(text=get_string(lang, "btn_addis"), callback_data="origin_Addis_Ababa"),
         InlineKeyboardButton(text=get_string(lang, "btn_oromia"), callback_data="origin_Oromia")],
        [InlineKeyboardButton(text=get_string(lang, "btn_amhara"), callback_data="origin_Amhara"),
         InlineKeyboardButton(text=get_string(lang, "btn_tigray"), callback_data="origin_Tigray")],
        [InlineKeyboardButton(text=get_string(lang, "btn_sidama"), callback_data="origin_Sidama"),
         InlineKeyboardButton(text=get_string(lang, "btn_snnpr"), callback_data="origin_SNNPR")],
        [InlineKeyboardButton(text=get_string(lang, "btn_other"), callback_data="origin_Other")]
    ]
    if "origin_region" in data:
        kb_buttons.append([InlineKeyboardButton(text=f"⏭️ Skip (Keep: {data['origin_region']})", callback_data="skip_origin")])
        
    kb = InlineKeyboardMarkup(inline_keyboard=kb_buttons)
    await message.answer(get_string(lang, "ask_origin"), reply_markup=kb)

@router.message(Onboarding.location)
async def fallback_location(message: Message, state: FSMContext):
    from src.bot.states import Onboarding
    await state.set_state(Onboarding.origin_region)

@router.callback_query(Onboarding.origin_region, F.data == "skip_origin")
async def skip_origin(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    data = await state.get_data()
    lang = get_lang(data)
    await prompt_bio(callback.message, lang, data)
    await callback.answer()

@router.callback_query(Onboarding.origin_region, F.data.startswith("origin_"))
async def process_origin_cb(callback: CallbackQuery, state: FSMContext):
    lang = get_lang(await state.get_data())
    origin = callback.data.split("_", 1)[1].replace("_", " ")
    await callback.message.edit_reply_markup(reply_markup=None)
    
    if origin == "Other":
        await callback.message.answer(get_string(lang, "ask_origin"))
        return
        
    await state.update_data(origin_region=origin)
    data = await state.get_data()
    await prompt_bio(callback.message, lang, data)
    await callback.answer()

@router.message(Onboarding.origin_region, F.text)
async def process_origin_text(message: Message, state: FSMContext):
    lang = get_lang(await state.get_data())
    await state.update_data(origin_region=message.text)
    data = await state.get_data()
    await prompt_bio(message, lang, data)

async def prompt_bio(message, lang, data):
    from src.bot.states import Onboarding
    text = get_string(lang, "ask_bio")
    if "bio" in data and data["bio"]:
        text += f"\n\n(Current: {data['bio']}. Type 'skip' to keep it.)"
        
    await message.answer(text)

@router.callback_query(Onboarding.origin_region)
async def fallback_origin(callback: CallbackQuery, state: FSMContext):
    from src.bot.states import Onboarding
    await state.set_state(Onboarding.bio)

@router.message(Onboarding.bio, F.text)
async def process_bio(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = get_lang(data)
    
    text = message.text.strip().lower()
    if text != "skip":
        await state.update_data(bio=message.text)
        
    # Just clear photos array initially in case they want to upload new ones.
    # But wait, if they skip uploading photos, we shouldn't delete old ones.
    await state.update_data(photos=[])
    
    text_photos = get_string(lang, "ask_photos")
    text_photos += "\n(If you already have photos, type 'skip' to keep them!)"
    await message.answer(text_photos)
    
    from src.bot.states import Onboarding
    await state.set_state(Onboarding.photos)

@router.message(Onboarding.photos, F.text)
async def skip_photos(message: Message, state: FSMContext):
    text = message.text.strip().lower()
    if text == "skip":
        await finalize_registration(message, state)
    else:
        data = await state.get_data()
        await message.answer(get_string(get_lang(data), "ask_photos"))

@router.message(Onboarding.photos, F.photo)
async def process_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = get_lang(data)
    photos = data.get("photos", [])
    file_id = message.photo[-1].file_id
    photos.append(file_id)
    await state.update_data(photos=photos)
    
    if len(photos) >= 2:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_string(lang, "btn_finish_register"), callback_data="finish_registration")]
        ])
        await message.answer(get_string(lang, "photo_received_done"), reply_markup=kb)
    else:
        await message.answer(get_string(lang, "photo_received_need_more"))

@router.callback_query(Onboarding.photos, F.data == "finish_registration")
async def process_photos_done(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = get_lang(data)
    message = callback.message
    
    if len(data.get("photos", [])) < 2:
        await callback.answer(get_string(lang, "ask_photos"), show_alert=True)
        return
        
    await callback.message.edit_reply_markup(reply_markup=None)
    await finalize_registration(message, state, callback.from_user)
    await callback.answer()

async def finalize_registration(message_or_call, state: FSMContext, from_user=None):
    if from_user is None:
        from_user = message_or_call.from_user
        
    data = await state.get_data()
    lang = get_lang(data)
    
    async with async_session_maker() as session:
        user = await session.get(User, from_user.id)
        if not user:
            user = User(telegram_id=from_user.id)
            session.add(user)
            
        user.telegram_username = from_user.username
        user.name = data["name"]
        user.age = data["age"]
        user.gender = data["gender"]
        user.gender_preference = data["gender_preference"]
        user.current_country = data.get("current_country", "Unknown")
        user.current_city = data.get("current_city", "Unknown")
        user.latitude = data.get("latitude")
        user.longitude = data.get("longitude")
        user.origin_region = data.get("origin_region", "Unknown")
        user.willing_to_relocate = data.get("willing_to_relocate", False)
        user.bio = data.get("bio", "")
        user.date_of_birth = data.get("dob_str", "")
        user.language_pref = lang

        new_photos = data.get("photos", [])
        if new_photos:
            # Delete old photos
            await session.execute(
                Photo.__table__.delete().where(Photo.user_id == from_user.id)
            )
            for i, file_id in enumerate(new_photos):
                photo = Photo(
                    user_id=from_user.id,
                    telegram_file_id=file_id,
                    sort_order=i,
                    is_primary=(i == 0)
                )
                session.add(photo)
                
        await session.commit()
        
    if isinstance(message_or_call, Message):
        await message_or_call.answer(get_string(lang, "profile_saved"), reply_markup=get_main_menu(lang))
    else:
        # It's actually a message object here
        await message_or_call.answer(get_string(lang, "profile_saved"), reply_markup=get_main_menu(lang))
        
    await state.clear()
