from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from sqlalchemy import select, and_, not_, or_
from src.database.session import async_session_maker
from src.database.models import User, Photo, Like, Match
from src.bot.locales import get_string
from aiogram.fsm.context import FSMContext
from typing import Optional

router = Router(name="discovery")


from sqlalchemy import desc

def format_profile(candidate: User, current_user: Optional[User] = None) -> str:
    from src.bot.locales import get_string
    lang = current_user.language_pref if current_user else "en"
    
    caption = f"{candidate.name}, {candidate.age}\n"
    caption += f"📍 {candidate.current_city}, {candidate.current_country}\n"
    caption += f"🌍 From: {candidate.origin_region}\n\n"
    
    if current_user:
        # Dynamic Shared Traits Highlight
        shared = []
        if candidate.current_city == current_user.current_city:
            shared.append(get_string(lang, "shared_city"))
        elif candidate.current_country == current_user.current_country:
            shared.append(get_string(lang, "shared_country"))
            
        if candidate.origin_region == current_user.origin_region:
            shared.append(get_string(lang, "shared_origin"))
            
        if shared:
            caption += f"{get_string(lang, 'shared_title')}\n"
            for trait in shared:
                caption += f"- {trait}\n"
            caption += "\n"
            
    if candidate.bio:
        caption += f"📝 {candidate.bio}"
        
    return caption

async def get_next_candidate(session, current_user: User) -> Optional[User]:
    if current_user.gender_preference.lower() == "both":
        gender_cond = True
    else:
        gender_cond = User.gender.ilike(current_user.gender_preference)
        
    pref_cond = or_(
        User.gender_preference.ilike(current_user.gender),
        User.gender_preference.ilike("both")
    )
    
    # Anti-Join for scalability
    stmt = (
        select(User)
        .outerjoin(Like, and_(
            Like.from_user_id == current_user.telegram_id,
            Like.to_user_id == User.telegram_id
        ))
        .where(
            and_(
                User.telegram_id != current_user.telegram_id,
                gender_cond,
                pref_cond,
                Like.id.is_(None)
            )
        )
        .order_by(
            desc(User.current_city == current_user.current_city),
            desc(User.current_country == current_user.current_country),
            desc(User.origin_region == current_user.origin_region)
        )
        .limit(1)
    )
    
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def send_candidate(message_or_call, lang: str, candidate: User, session, current_user: User):
    photo_stmt = select(Photo).where(and_(Photo.user_id == candidate.telegram_id, Photo.is_primary == True)).limit(1)
    photo_res = await session.execute(photo_stmt)
    photo = photo_res.scalar_one_or_none()
    
    if not photo:
        photo_stmt = select(Photo).where(Photo.user_id == candidate.telegram_id).limit(1)
        photo_res = await session.execute(photo_stmt)
        photo = photo_res.scalar_one_or_none()
        
    caption = format_profile(candidate, current_user)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_string(lang, "btn_pass"), callback_data=f"discover_pass_{candidate.telegram_id}"),
         InlineKeyboardButton(text=get_string(lang, "btn_like"), callback_data=f"discover_like_{candidate.telegram_id}")]
    ])
    
    if isinstance(message_or_call, Message):
        if photo:
            await message_or_call.answer_photo(photo.telegram_file_id, caption=caption, reply_markup=kb, parse_mode="Markdown")
        else:
            await message_or_call.answer(caption, reply_markup=kb, parse_mode="Markdown")
    else:
        if photo:
            try:
                await message_or_call.message.edit_media(
                    media=InputMediaPhoto(media=photo.telegram_file_id, caption=caption, parse_mode="Markdown"),
                    reply_markup=kb
                )
            except Exception:
                await message_or_call.message.delete()
                await message_or_call.message.answer_photo(photo.telegram_file_id, caption=caption, reply_markup=kb, parse_mode="Markdown")
        else:
            try:
                await message_or_call.message.edit_text(caption, reply_markup=kb, parse_mode="Markdown")
            except Exception:
                pass
async def cmd_discover(message: Message, state: FSMContext):
    async with async_session_maker() as session:
        user = await session.get(User, message.from_user.id)
        if not user:
            await message.answer("Please complete your profile first using /start.")
            return
            
        candidate = await get_next_candidate(session, user)
        if candidate:
            await send_candidate(message, user.language_pref, candidate, session, user)
        else:
            await message.answer(get_string(user.language_pref, "no_more_profiles"))

@router.message(F.text.in_(["👤 My Profile", "👤 ፕሮፋይሌ"]))
async def cmd_my_profile(message: Message, state: FSMContext):
    async with async_session_maker() as session:
        user = await session.get(User, message.from_user.id)
        if not user:
            await message.answer("Please complete your profile first using /start.")
            return
            
        lang = user.language_pref
        caption = get_string(lang, "profile_caption").format(
            name=user.name,
            age=user.age,
            city=user.current_city,
            country=user.current_country,
            origin=user.origin_region,
            bio=user.bio or ""
        )
        
        photo_stmt = select(Photo).where(and_(Photo.user_id == user.telegram_id, Photo.is_primary == True)).limit(1)
        photo_res = await session.execute(photo_stmt)
        photo = photo_res.scalar_one_or_none()
        
        if photo:
            await message.answer_photo(
                photo.telegram_file_id, 
                caption=caption,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="✏️ Edit Profile", callback_data="edit_profile")]
                ])
            )
        else:
            await message.answer(
                caption,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="✏️ Edit Profile", callback_data="edit_profile")]
                ])
            )

@router.callback_query(F.data == "edit_profile")
async def process_edit_profile(callback: CallbackQuery, state: FSMContext):
    # Route back to onboarding
    await callback.message.answer(
        "Let's update your profile! We will start from the beginning.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="English 🇺🇸", callback_data="lang_en"),
             InlineKeyboardButton(text="አማርኛ 🇪🇹", callback_data="lang_am")]
        ])
    )
    from src.bot.states import Onboarding
    await state.set_state(Onboarding.language)
    await callback.answer()

async def send_match_page(message_or_call, user: User, session, page: int):
    # Fetch all matches for the user
    stmt = select(Match).where(or_(Match.user_a_id == user.telegram_id, Match.user_b_id == user.telegram_id)).order_by(Match.created_at.desc())
    result = await session.execute(stmt)
    matches = result.scalars().all()
    
    if not matches:
        text = "You don't have any matches yet. Keep swiping! 🔍"
        if isinstance(message_or_call, Message):
            await message_or_call.answer(text)
        else:
            await message_or_call.message.edit_text(text)
        return
        
    total = len(matches)
    if page >= total:
        page = total - 1
    if page < 0:
        page = 0
        
    m = matches[page]
    partner_id = m.user_b_id if m.user_a_id == user.telegram_id else m.user_a_id
    partner = await session.get(User, partner_id)
    
    if not partner:
        return
        
    photo_stmt = select(Photo).where(and_(Photo.user_id == partner.telegram_id, Photo.is_primary == True)).limit(1)
    photo_res = await session.execute(photo_stmt)
    photo = photo_res.scalar_one_or_none()
    
    link = f"https://t.me/{partner.telegram_username}" if partner.telegram_username else f"tg://user?id={partner_id}"
    
    caption = f"💬 **Match {page + 1} of {total}**\n\n"
    caption += f"👤 {partner.name}, {partner.age}\n"
    caption += f"📍 {partner.current_city}, {partner.current_country}"
    
    # Pagination buttons
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Previous", callback_data=f"matchpage_{page - 1}"))
    if page < total - 1:
        nav_buttons.append(InlineKeyboardButton(text="Next ➡️", callback_data=f"matchpage_{page + 1}"))
        
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"💬 Message {partner.name}", url=link)],
        nav_buttons
    ])
    
    if isinstance(message_or_call, Message):
        if photo:
            await message_or_call.answer_photo(photo.telegram_file_id, caption=caption, parse_mode="Markdown", reply_markup=kb)
        else:
            await message_or_call.answer(caption, parse_mode="Markdown", reply_markup=kb)
    else:
        if photo:
            try:
                await message_or_call.message.edit_media(
                    media=InputMediaPhoto(media=photo.telegram_file_id, caption=caption, parse_mode="Markdown"),
                    reply_markup=kb
                )
            except Exception:
                await message_or_call.message.delete()
                await message_or_call.message.answer_photo(photo.telegram_file_id, caption=caption, parse_mode="Markdown", reply_markup=kb)
        else:
            try:
                await message_or_call.message.edit_text(caption, parse_mode="Markdown", reply_markup=kb)
            except Exception:
                pass


@router.message(F.text.in_(["💬 My Matches", "💬 ተዛማጆች"]))
async def cmd_my_matches(message: Message, state: FSMContext):
    async with async_session_maker() as session:
        user = await session.get(User, message.from_user.id)
        if not user:
            return
        await send_match_page(message, user, session, 0)

@router.callback_query(F.data.startswith("matchpage_"))
async def process_match_page(callback: CallbackQuery):
    page = int(callback.data.split("_")[1])
    async with async_session_maker() as session:
        user = await session.get(User, callback.from_user.id)
        if user:
            await send_match_page(callback, user, session, page)
    await callback.answer()

@router.callback_query(F.data.startswith("discover_"))
async def process_discover_action(callback: CallbackQuery):
    parts = callback.data.split("_")
    action = parts[1] # "like" or "pass"
    target_id = int(parts[2])
    
    if action == "like":
        await callback.answer("❤️ Loved!")
        try:
            from aiogram.types import ReactionTypeEmoji
            await callback.message.react([ReactionTypeEmoji(type="emoji", emoji="❤️")])
            import asyncio
            await asyncio.sleep(0.6) # Let the animation play
        except Exception:
            pass
    else:
        await callback.answer("👎 Passed")
        
    async with async_session_maker() as session:
        user = await session.get(User, callback.from_user.id)
        if not user:
            return
            
        new_like = Like(
            from_user_id=user.telegram_id,
            to_user_id=target_id,
            is_like=(action == "like")
        )
        session.add(new_like)
        
        if action == "like":
            mutual_stmt = select(Like).where(and_(Like.from_user_id == target_id, Like.to_user_id == user.telegram_id, Like.is_like == True))
            mutual_res = await session.execute(mutual_stmt)
            if mutual_res.scalar_one_or_none():
                match = Match(user_a_id=user.telegram_id, user_b_id=target_id)
                session.add(match)
                
                target_user = await session.get(User, target_id)
                
                target_link = f"https://t.me/{target_user.telegram_username}" if target_user.telegram_username else f"tg://user?id={target_id}"
                user_link = f"https://t.me/{user.telegram_username}" if user.telegram_username else f"tg://user?id={user.telegram_id}"
                
                user_match_msg = get_string(user.language_pref, "match_found").format(name=target_user.name, link=target_link)
                target_match_msg = get_string(target_user.language_pref, "match_found").format(name=user.name, link=user_link)
                
                try:
                    await callback.bot.send_message(target_id, target_match_msg)
                except Exception:
                    pass
                    
                await callback.message.answer(user_match_msg)
        
        await session.commit()
        
        candidate = await get_next_candidate(session, user)
        if candidate:
            await send_candidate(callback, user.language_pref, candidate, session, user)
        else:
            await callback.message.delete()
            await callback.message.answer(get_string(user.language_pref, "no_more_profiles"))
