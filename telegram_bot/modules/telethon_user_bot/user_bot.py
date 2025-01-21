import logging
import random
import traceback
import os

from telethon import TelegramClient
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.errors.rpcerrorlist import (
    InviteHashInvalidError,
    InviteHashExpiredError,
    UserAlreadyParticipantError,
    UserIsBlockedError
)
from telethon.errors import UserDeactivatedError
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.types import MessageMediaPhoto
from telethon.sync import functions
from telegram_bot.admin_app.db_requests import set_unactive_account
import markdown

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
                return False, "not_authorized"

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

                channel = await client.get_entity(channel_url)
                channel_id = channel.id  # This gives you the ID of the channel
                logger.info(f"Channel ID: {channel_id}")

                logger.info("Successfully joined the channel or group.")
                return True, "free", channel_id

            except UserAlreadyParticipantError:
                logger.error("User is already a member of the channel or group.")
                return False, "in_channel"

            except InviteHashInvalidError:
                logger.error("Invalid invite hash. The link is incorrect or expired.")
                return False, "invalid_link"

            except InviteHashExpiredError:
                logger.error("Invite link has expired.")
                return False, "expired_link"

            except ValueError:
                logger.error(
                    "Could not resolve the channel. Check if it exists or is private."
                )
                return False, "invalid_channel"

            finally:
                # Disconnect the client at the end
                await client.disconnect()

        except Exception:
            logger.error("Error while joining the channel or group.")
            logger.error(traceback.format_exc())
            if client and client.is_connected():
                await client.disconnect()
            return False, "error"

    async def get_new_posts(
        self,
        phone_number: str,
        api_id: int,
        api_hash: int,
        limit: int = 1,
        channels: dict = [],
    ):
        """
        Get new posts from all channels
        """
        try:
            client = TelegramClient(f"sessions/{phone_number}", api_id, api_hash)
            await client.connect()

            # check if client is authorized
            if not await client.is_user_authorized():
                logger.error(
                    "Client is not authorized. Please authorize first."
                )
                await client.disconnect()
                return False
            
            # get all dialogs
            dialogs = await client.get_dialogs()
            posts_with_images = []
            chats_with_unread = []

            for channel in channels:
                for dialog in dialogs:
                    channel_id = getattr(dialog.message.peer_id, 'channel_id', None)
                    if channel_id is not None:
                        if channels.get(channel)[2] == str(channel_id):
                            # check if there are unread messages
                            if dialog.unread_count > 0:
                                chats_with_unread.append(dialog)

            if not chats_with_unread:
                logger.info("Don't have new posts")
                await client.disconnect()
                return []

            # create the "images" directory if it doesn't exist
            os.makedirs("images", exist_ok=True)

            # loop through all unread chats
            for chat in chats_with_unread:
                chat_name = chat.name or "Без назви"
                dt = chat.date
                logger.info(f"Checking chat: {chat_name}")

                # get the last message
                messages = await client.get_messages(chat.entity, limit=limit)

                # filter out non-text messages
                post = {"chat": f"{chat_name} {dt.strftime("%H:%M:%S %d-%m-%y")}", "message": markdown.markdown(messages[0].text)}

                # if the message has a photo
                if isinstance(messages[0].media, MessageMediaPhoto):
                    # download the photo
                    file_path = await client.download_media(
                        messages[0].media, file="images/"
                    )
                    post["image_path"] = file_path  # save the path to the image

                posts_with_images.append(post)

                await client.send_read_acknowledge(
                    chat.entity,
                    message=messages,
                    clear_mentions=False,
                    clear_reactions=False
                )

            # disconnect the client
            await client.disconnect()

            if not posts_with_images:
                logger.info("New posts not found.")
                return []

            return posts_with_images
        except (UserDeactivatedError, UserIsBlockedError) as e:
            logger.error(f"Error: account {phone_number} is deactivated.")
            logger.error(str(e))
            await set_unactive_account(phone_number)
            if client and client.is_connected():
                await client.disconnect()
            return False
        
        except Exception:
            logger.error("Error while getting new posts.")
            logger.error(f"{traceback.format_exc()}")
            if client and client.is_connected():
                await client.disconnect()
            return False
