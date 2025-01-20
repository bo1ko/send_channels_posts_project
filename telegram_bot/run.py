import traceback
import logging
import asyncio
import sys
import os


from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram import types
from aiogram.enums import ParseMode

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import django_setup

from telegram_bot.admin_app.handlers import router as admin_router
from telegram_bot.admin_app.common import private as admin_private


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[logging.FileHandler("logs/bot.log"), logging.StreamHandler()],
)

logger = logging.getLogger(__name__)

bot = Bot(
    token=os.getenv("BOT_TOKEN"),
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)


async def main():
    logger.info("Starting bot")
    dp = Dispatcher()
    dp.include_router(admin_router)

    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_my_commands(
        commands=admin_private, scope=types.BotCommandScopeAllPrivateChats()
    )

    await dp.start_polling(bot)

    logger.info("Bot stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot is stopped manually")
    except Exception:
        logger.error("Bot stops with an error")
        logger.info(f"{traceback.format_exc()}")
