import asyncio
import logging
import sys
import os
import traceback

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import django_setup
import telegram_bot.admin_app.db_requests as rq

from telegram_bot.modules.telethon_user_bot.user_bot import UserBot
from telegram_bot.modules.telethon_user_bot.utils import send_email
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


async def user_bot_new_messages():
    user_bot = UserBot()
    telegram_accounts = await rq.get_telegram_accounts()

    try:
        if telegram_accounts:
            for key, value in telegram_accounts.items():
                phone_number = key
                api_id = int(value[2])
                api_hash = value[3]

                channels = await rq.get_telegram_channels()
                results = await user_bot.get_new_posts(
                    phone_number, api_id, api_hash, channels=channels
                )

                if results:
                    from_email = os.getenv("FROM_EMAIL")
                    to_email = os.getenv("TO_EMAIL")
                    smtp_server = os.getenv("SMTP_SERVER")
                    smtp_port = os.getenv("SMTP_PORT")
                    smtp_user = os.getenv("SMTP_USER")
                    smtp_password = os.getenv("SMTP_PASSWORD")

                    for result in results:
                        if result:
                            send_email(
                                result["chat"],
                                result["message"],
                                to_email,
                                from_email,
                                smtp_server,
                                smtp_port,
                                smtp_user,
                                smtp_password,
                                result.get("image_path"),
                            )

        else:
            logger.error("No Telegram accounts found")
            return

    except Exception:
        logger.error("user_bot_new_messages error")
        logger.error(f"{traceback.format_exc()}")


def start_cron():
    asyncio.run(user_bot_new_messages())