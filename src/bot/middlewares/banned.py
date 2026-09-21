from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject
from src.database.session import async_session_maker
from src.database.models import User, UserStatus
from src.bot.locales import get_string

class BannedMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        
        # Determine the user ID based on the event type
        user_id = None
        lang = "en"
        
        if isinstance(event, Message):
            user_id = event.from_user.id
            message_or_call = event
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
            message_or_call = event.message
            
        if user_id:
            async with async_session_maker() as session:
                user = await session.get(User, user_id)
                if user:
                    lang = user.language_pref
                    if user.status == UserStatus.BANNED:
                        # User is banned, block the update
                        msg = "Your account has been suspended by an administrator."
                        if lang == "am":
                            msg = "አካውንትዎ በአስተዳዳሪ ታግዷል።"
                            
                        if isinstance(event, CallbackQuery):
                            await event.answer(msg, show_alert=True)
                        elif isinstance(event, Message):
                            await event.answer(msg)
                            
                        return # Stop propagation
        
        return await handler(event, data)
