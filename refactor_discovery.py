import re

with open('src/bot/handlers/discovery.py', 'r', encoding='utf-8') as f:
    content = f.read()

replacement = '''
from sqlalchemy import desc

def format_profile(candidate: User, current_user: Optional[User] = None) -> str:
    caption = f"{candidate.name}, {candidate.age}\\n"
    caption += f"📍 {candidate.current_city}, {candidate.current_country}\\n"
    caption += f"🌍 From: {candidate.origin_region}\\n\\n"
    
    if current_user:
        # Dynamic Shared Traits Highlight
        shared = []
        if candidate.current_city == current_user.current_city:
            shared.append("📍 You both live in the same city!")
        elif candidate.current_country == current_user.current_country:
            shared.append("📍 You both live in the same country!")
            
        if candidate.origin_region == current_user.origin_region:
            shared.append("🌍 You are from the same origin region!")
            
        if shared:
            caption += "✨ **What you have in common:**\\n"
            for trait in shared:
                caption += f"- {trait}\\n"
            caption += "\\n"
            
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
'''

import re
# We need to replace `async def get_next_candidate` and `async def send_candidate` entirely.
# Let's just find them and replace.

start_str = "async def get_next_candidate(session, current_user: User) -> Optional[User]:"
end_str = "async def cmd_discover(message: Message, state: FSMContext):"

start_idx = content.find(start_str)
end_idx = content.find(end_str)

new_content = content[:start_idx] + replacement + "\\n" + content[end_idx:]

with open('src/bot/handlers/discovery.py', 'w', encoding='utf-8') as f:
    f.write(new_content)
