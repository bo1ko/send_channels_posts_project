import logging
import random
import traceback
import os

from telethon import TelegramClient
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.errors.rpcerrorlist import InviteHashInvalidError, InviteHashExpiredError, UserAlreadyParticipantError
from telethon.tl.functions.messages import ImportChatInviteRequest

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
        except Exception:
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
        except Exception:
            logger.error("Phone code error")
            logger.error(f"{traceback.format_exc()}")
            client.disconnect()
            return False

    async def join_channel(
        self, channel_url: str, phone_number: str, api_id: int, api_hash: str
    ):
        """
        Joins a Telegram channel or group, handling both public and private invite links.
        """

        try:
            # Initialize the Telegram client with a session per phone number
            client = TelegramClient(f"sessions/{phone_number}", api_id, api_hash)
            await client.connect()

            # Ensure the user is authorized
            if not await client.is_user_authorized():
                logger.error("Client is not authorized. Please authorize first.")
                await client.disconnect()
                return False

            try:
                # Handle private invite links (t.me/+ or /joinchat/)
                if "/joinchat/" in channel_url or "t.me/+" in channel_url:
                    # Extract the invite hash and strip any leading '+'
                    invite_hash = channel_url.split("/")[-1].lstrip("+")
                    logger.info(
                        f"Joining private group using invite link: {channel_url}"
                    )
                    await client(ImportChatInviteRequest(invite_hash))

                else:
                    # Handle public channels
                    logger.info(f"Joining public channel or group: {channel_url}")
                    await client(JoinChannelRequest(channel_url))

                logger.info("Successfully joined the channel or group.")
                return True
            
            except UserAlreadyParticipantError:
                logger.error("User is already a member of the channel or group.")
                return False, "in_channel"

            except InviteHashInvalidError:
                logger.error("Invalid invite hash. The link is incorrect or expired.")
                return False

            except InviteHashExpiredError:
                logger.error("Invite link has expired.")
                return False

            except ValueError:
                logger.error(
                    "Could not resolve the channel. Check if it exists or is private."
                )
                return False

            finally:
                # Disconnect the client at the end
                await client.disconnect()

        except Exception:
            logger.error("Error while joining the channel or group.")
            logger.error(traceback.format_exc())
            if client and client.is_connected():
                await client.disconnect()
            return False
