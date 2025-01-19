import logging
import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram import types
from aiogram.enums import ParseMode

from admin.handlers import router
from admin.common import private

# from telethon_user_bot.user_bot import UserBot

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
    logger.info("Bot start")
    dp = Dispatcher()
    dp.include_routers(admin_router)

    commands = [admin_private]

    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_my_commands(
        commands=commands, scope=types.BotCommandScopeAllPrivateChats()
    )
    await dp.start_polling(bot)
    logger.info("Bot exit")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot is stopped manually")
    except Exception as e:
        logger.error("Bot stops with an error")
        logger.info(e.with_traceback)
