from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select, func

from src.database.session import async_session_maker
from src.database.models import User, UserStatus, Match, Like
from src.config import settings

router = Router()

def is_admin(user_id: int) -> bool:
    return user_id in settings.get_admin_ids

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        return
        
    text = (
        "🛠 **Admin Panel**\n\n"
        "Available Commands:\n"
        "/stats - View platform statistics\n"
        "/ban <username_or_id> - Ban a user\n"
        "/unban <username_or_id> - Unban a user\n"
    )
    await message.answer(text, parse_mode="Markdown")

@router.message(Command("stats"))
async def cmd_stats(message: Message):
    if not is_admin(message.from_user.id):
        return
        
    async with async_session_maker() as session:
        # Total users
        users_res = await session.execute(select(func.count(User.telegram_id)))
        total_users = users_res.scalar()
        
        # Total matches
        matches_res = await session.execute(select(func.count(Match.id)))
        total_matches = matches_res.scalar()
        
        # Total likes
        likes_res = await session.execute(select(func.count(Like.id)).where(Like.is_like == True))
        total_likes = likes_res.scalar()
        
        text = (
            "📊 **Platform Statistics**\n\n"
            f"👥 Total Users: {total_users}\n"
            f"❤️ Total Swipes/Likes: {total_likes}\n"
            f"🔥 Total Matches: {total_matches}"
        )
        await message.answer(text, parse_mode="Markdown")

async def get_target_user(session, query: str):
    if query.isdigit():
        return await session.get(User, int(query))
    else:
        username = query.replace("@", "").strip()
        stmt = select(User).where(User.telegram_username.ilike(username))
        res = await session.execute(stmt)
        return res.scalar_one_or_none()

@router.message(Command("ban"))
async def cmd_ban(message: Message):
    if not is_admin(message.from_user.id):
        return
        
    parts = message.text.split(" ", 1)
    if len(parts) < 2:
        await message.answer("Usage: /ban <username_or_id>")
        return
        
    query = parts[1]
    async with async_session_maker() as session:
        user = await get_target_user(session, query)
        if not user:
            await message.answer("User not found in database.")
            return
            
        user.status = UserStatus.BANNED
        await session.commit()
        await message.answer(f"✅ User {user.name} (@{user.telegram_username}) has been banned.")

@router.message(Command("unban"))
async def cmd_unban(message: Message):
    if not is_admin(message.from_user.id):
        return
        
    parts = message.text.split(" ", 1)
    if len(parts) < 2:
        await message.answer("Usage: /unban <username_or_id>")
        return
        
    query = parts[1]
    async with async_session_maker() as session:
        user = await get_target_user(session, query)
        if not user:
            await message.answer("User not found in database.")
            return
            
        user.status = UserStatus.ACTIVE
        await session.commit()
        await message.answer(f"✅ User {user.name} (@{user.telegram_username}) has been unbanned.")
