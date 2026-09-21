import asyncio
import logging
import sys
import os
from aiohttp import web

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from src.config import settings

async def health_check(request):
    return web.Response(text="Bot is running!")

async def start_dummy_server():
    app = web.Application()
    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)
    
    port = int(os.environ.get("PORT", 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logging.info(f"Dummy web server started on port {port}")

async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
    
    if settings.bot_token == "your_telegram_bot_token_here":
        logging.error("Please set a valid BOT_TOKEN in your .env file.")
        return

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    from src.bot.handlers import onboarding, discovery, safety, admin
    from src.bot.middlewares.banned import BannedMiddleware
    
    # Register Middleware
    dp.message.middleware(BannedMiddleware())
    dp.callback_query.middleware(BannedMiddleware())
    
    # Register Routers
    dp.include_routers(admin.router, onboarding.router, discovery.router, safety.router)
    
    # Start the dummy web server so Render's Web Service health check passes
    await start_dummy_server()
    
    logging.info("Starting bot in polling mode...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped!")
