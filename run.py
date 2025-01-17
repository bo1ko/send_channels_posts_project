import logging
import asyncio


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[logging.FileHandler("logs/bot.log"), logging.StreamHandler()],
)

logger = logging.getLogger(__name__)

async def main():
    logger.info("Bot start")
    logger.info("Bot exit")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot is stopped manually")
    except Exception as e:
        logger.error("Bot stops with an error")
        logger.info(e.with_traceback)
