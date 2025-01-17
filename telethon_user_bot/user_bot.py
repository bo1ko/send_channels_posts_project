import logging

from telethon import TelegramClient
from aiogram.types import Message


logger = logging.getLogger(__name__)


class UserBot:
    def __init__(self, message: Message):
        message: Message = message

    async def auth(phone_number: str, api_id: int, api_hash: str):
        """
        Authorizes userbot in Telegram

        :param phone_number: 
        """
        try:
            client = TelegramClient(phone_number, api_id, api_hash)

            if not await client.is_user_authorized():
                await client.send_code_request(phone_number)

                code = input("Code: ")

                try:
                    await client.sign_in(phone=phone_number, code=code)
                except Exception as e:
                    logger.error("Phone code error")
                    logger.info(e.with_traceback)
        except Exception as e:
            logger.error("Auth method error")
            logger.info(e.with_traceback)
