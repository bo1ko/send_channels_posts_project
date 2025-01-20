import logging
import os
import traceback

from custom_admin.models import TelegramChannel, TelegramUser, CustomUser, TelegramAccount
from asgiref.sync import sync_to_async
from django.db.models import Count

logger = logging.getLogger(__name__)


@sync_to_async
def get_or_create_user(user_id):
    return TelegramUser.objects.get_or_create(telegram_id=user_id)


@sync_to_async
def is_user_admin(user_id):
    try:
        telegram = TelegramUser.objects.get(telegram_id=user_id)
        return CustomUser.objects.get(telegram=telegram).is_superuser
    except TelegramUser.DoesNotExist:
        return False
    except CustomUser.DoesNotExist:
        return False
    except Exception:
        logger.error("db_requests.is_user_admin error")
        logger.error(f"{traceback.format_exc()}")
        return False


@sync_to_async
def get_telegram_accounts():
    accounts = TelegramAccount.objects.all()
    accounts_dict = {}

    for account in accounts:
        accounts_dict[account.phone_number] = [account.pk, account.is_active]
    
    return accounts_dict

@sync_to_async
def remove_telegram_account(url: str):
    return TelegramAccount.objects.get(url=url).delete()


@sync_to_async
def delete_telegram_account(pk: int):
    phone_number = TelegramAccount.objects.get(pk=pk).phone_number
    session_file_path = f"sessions/{phone_number}.session"

    if os.path.exists(session_file_path):
        os.remove(session_file_path)

    return TelegramAccount.objects.get(pk=pk).delete()

@sync_to_async
def get_telegram_channels():
    channels = TelegramChannel.objects.all()
    channels_dict = {}

    for channel in channels:
        channels_dict[channel.pk] = [channel.title, channel.url]

    return channels_dict

@sync_to_async
def get_or_create_telegram_channel(title: str, url: str, telegram: TelegramAccount):
    return TelegramChannel.objects.get_or_create(url=url, defaults={"title": title, "telegram_account": telegram})

@sync_to_async
def delete_telegram_channel(pk: int):
    return TelegramChannel.objects.get(pk=pk).delete()

@sync_to_async
def get_min_telegram_channel():
    accounts_with_channel_count = TelegramAccount.objects.annotate(
        channel_count=Count('telegramchannel')
    )

    min = 0
    min_account = None
    for account in accounts_with_channel_count:
        if account.channel_count >= min:
            min = account.channel_count
            min_account = account

    return min_account
