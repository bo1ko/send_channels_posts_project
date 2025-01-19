import logging
import random
import traceback
import os

from telethon import TelegramClient

logger = logging.getLogger(__name__)


class UserBot:
    async def auth_first_step(self, phone_number: str, api_id: int, api_hash: str):
        """
        Authorizes userbot in Telegram / first step.
        """

        try:
            if not os.path.exists("sessions"):
                os.makedirs("sessions")

            device_models = [
                "Android-9",
                "Android-10",
                "Android-11",
                "Android-12",
                "iPhone-12",
                "iPhone-13",
                "Samsung-Galaxy-S21",
                "Google-Pixel-6",
                "Huawei-P30",
                "Xiaomi-Redmi-Note-10",
                "OnePlus-9",
                "Nokia-8.3",
                "LG-V60",
                "Motorola-Moto-G100",
            ]

            random_device = random.choice(device_models)

            client = TelegramClient(
                f"sessions/{phone_number}", api_id, api_hash, device_model=random_device
            )

            await client.connect()

            if not await client.is_user_authorized():
                await client.send_code_request(phone_number)

                return client
        except Exception as e:
            logger.error("Auth method error")
            logger.error(f"{traceback.format_exc()}")
            client.disconnect()
            return False

    async def auth_second_step(
        self, code: str, phone_number: str, client: TelegramClient
    ):
        """
        Authorizes userbot in Telegram / second step.
        """

        try:
            await client.sign_in(phone=phone_number, code=code)
            client.disconnect()
            return f"sessions/{phone_number}"
        except Exception as e:
            logger.error("Phone code error")
            logger.error(f"{traceback.format_exc()}")
            client.disconnect()
            return False
    
