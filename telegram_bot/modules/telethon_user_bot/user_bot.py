import asyncio
import logging
import os
import pathlib

from telethon import TelegramClient
from aiogram.types import Message


logger = logging.getLogger(__name__)


class UserBot:
    async def auth_first_step(self, phone_number: str, api_id: int, api_hash: str):
        """
        Authorizes userbot in Telegram / first step.
        """

        try:
            if not os.path.exists("logs"):
                os.makedirs("logs")

            client = TelegramClient(f"sessions/{phone_number}", api_id, api_hash)

            await client.connect()

            if not await client.is_user_authorized():
                await client.send_code_request(phone_number)

                return client
        except Exception as e:
            logger.error("Auth method error")
            logger.error(f"{e.with_traceback}")
            return False

    async def auth_second_step(
        self, code: str, phone_number: str, client: TelegramClient
    ):
        """
        Authorizes userbot in Telegram / second step.
        """

        try:
            await client.sign_in(phone=phone_number, code=code)
            return f"sessions/{phone_number}"
        except Exception as e:
            logger.error("Phone code error")
            logger.error(e.with_traceback)
            return False
