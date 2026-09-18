import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from src.config import settings

async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
    
    # We will initialize the bot later when a token is provided
    if settings.bot_token == "your_telegram_bot_token_here":
        logging.error("Please set a valid BOT_TOKEN in your .env file.")
        return

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # Import and include routers here later
    from src.bot.handlers import onboarding, discovery, safety
    dp.include_routers(onboarding.router, discovery.router, safety.router)
    
    logging.info("Starting bot in polling mode...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped!")
