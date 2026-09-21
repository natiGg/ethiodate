from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, LabeledPrice, PreCheckoutQuery, InlineKeyboardMarkup, InlineKeyboardButton

from src.database.session import async_session_maker
from src.database.models import User
from src.bot.locales import get_string

router = Router()

@router.message(Command("help"))
async def cmd_help(message: Message):
    async with async_session_maker() as session:
        user = await session.get(User, message.from_user.id)
        lang = user.language_pref if user else "en"
        
    text = (
        "🤖 **Help & Support**\n\n"
        "Welcome to the Ethiopian Dating Bot! Here are some tips to get started:\n\n"
        "🔍 **Discover**: Find new people. You can skip or like them.\n"
        "💬 **My Matches**: See the people who liked you back! You will get their Telegram link to chat.\n"
        "👤 **My Profile**: View or edit your current profile.\n\n"
        "If you encounter any issues, please contact the admin team."
    )
    if lang == "am":
        text = (
            "🤖 **እርዳታ እና ድጋፍ**\n\n"
            "ወደ ኢትዮጵያ የፍቅር ጓደኛ መፈለጊያ ቦት በደህና መጡ! ለመጀመር የሚረዱዎት መመሪያዎች:\n\n"
            "🔍 **Discover**: አዳዲስ ሰዎችን ያግኙ። ማለፍ ወይም መውደድ ይችላሉ።\n"
            "💬 **My Matches**: እርስዎንም የወደዱዎትን ሰዎች ይመልከቱ! ለመወያየት የቴሌግራም ሊንካቸውን ያገኛሉ።\n"
            "👤 **My Profile**: የአሁኑን ፕሮፋይልዎን ይመልከቱ ወይም ያስተካክሉ።\n\n"
            "ማንኛውም ችግር ካጋጠመዎት እባክዎ አስተዳዳሪዎችን ያነጋግሩ።"
        )
        
    await message.answer(text, parse_mode="Markdown")

@router.message(Command("donate"))
async def cmd_donate(message: Message):
    async with async_session_maker() as session:
        user = await session.get(User, message.from_user.id)
        lang = user.language_pref if user else "en"
        
    text = "⭐️ **Support the Bot!**\n\nChoose an amount to donate using Telegram Stars. Your support helps keep the bot running and free!"
    if lang == "am":
        text = "⭐️ **ቦቱን ይደግፉ!**\n\nበቴሌግራም ስታርስ (Stars) በመጠቀም ለመለገስ መጠኑን ይምረጡ። የእርስዎ ድጋፍ ቦቱ በነፃ አገልግሎት መስጠቱን እንዲቀጥል ይረዳል!"
        
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐️ 50 Stars", callback_data="donate_50"),
         InlineKeyboardButton(text="⭐️ 100 Stars", callback_data="donate_100")],
        [InlineKeyboardButton(text="⭐️ 500 Stars", callback_data="donate_500")]
    ])
    
    await message.answer(text, parse_mode="Markdown", reply_markup=kb)

@router.callback_query(F.data.startswith("donate_"))
async def process_donate_callback(callback: CallbackQuery):
    amount = int(callback.data.split("_")[1])
    
    prices = [LabeledPrice(label="Donation", amount=amount)]
    
    # Telegram Stars uses empty provider token and "XTR" currency
    await callback.message.answer_invoice(
        title=f"Donate {amount} Stars",
        description="Thank you for supporting the Ethiopian Dating Bot!",
        payload=f"donation_{amount}_{callback.from_user.id}",
        provider_token="", 
        currency="XTR",
        prices=prices
    )
    await callback.answer()

@router.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)

@router.message(F.successful_payment)
async def successful_payment_handler(message: Message):
    async with async_session_maker() as session:
        user = await session.get(User, message.from_user.id)
        lang = user.language_pref if user else "en"
        
    text = "🎉 **Thank you so much for your donation!** Your support is highly appreciated."
    if lang == "am":
        text = "🎉 **ስለ እርዳታዎ በጣም እናመሰግናለን!** ድጋፍዎ ትልቅ ትርጉም አለው።"
        
    await message.answer(text, parse_mode="Markdown")
