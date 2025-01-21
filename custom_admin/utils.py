from django.db.models import Count
from .models import TelegramAccount, TelegramChannel


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

def get_or_create_telegram_channel(title: str, url: str, telegram: TelegramAccount, channel_id: str):
    return TelegramChannel.objects.get_or_create(url=url, defaults={"title": title, "telegram_account": telegram, "channel_id": channel_id})
