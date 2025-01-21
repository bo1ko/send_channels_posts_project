import asyncio
import json
import logging
from django.http import JsonResponse
from django.shortcuts import redirect, render

from cron import start_cron
from telegram_bot.modules.telethon_user_bot.user_bot import UserBot
from .models import TelegramChannel
from django.contrib import messages
from .utils import get_min_telegram_channel, get_or_create_telegram_channel

logger = logging.getLogger(__name__)


def index(request):
    channels = TelegramChannel.objects.all()

    context = {"channels": channels}

    return render(request, "custom_admin/index.html", context)


def add_channel(request):
    if request.method == "POST":
        try:
            channel_name = request.POST.get("name")
            channel_url = request.POST.get("url")

            # Perform your logic here, such as saving to the database
            if not channel_name or not channel_url:
                return redirect("custom_admin:add_channel")
            else:
                account = get_min_telegram_channel()

                if not account:
                    messages.error(
                        request, "Добавте спочатку аккаунт, щоб додати канал!"
                    )
                    return redirect("custom_admin:add_channel")

                user_bot = UserBot()
                result = asyncio.run(
                    user_bot.join_channel(
                        channel_url,
                        account.phone_number,
                        account.api_id,
                        account.api_hash,
                    )
                )

                if result[1] == "in_channel":
                    messages.error(request, "Користувач вже є у каналі!")
                    return redirect("custom_admin:add_channel")
                elif result[1] == "free":
                    channel, created = get_or_create_telegram_channel(
                        channel_name, channel_url, account, channel_id=result[2]
                    )

                    if not created:
                        messages.error(request, "Канал вже існує!")
                        return redirect("custom_admin:add_channel")
                if result:
                    messages.success(request, "Канал успішно додано!")
                    return redirect("custom_admin:add_channel")
                else:
                    messages.error(
                        request, "Помилка при додаванні каналу. Спробуйте знову 🔃"
                    )
                    return redirect("custom_admin:add_channel")

        except Exception as e:
            print(e)
            logger.error(f"add_channel error: {e}")
            messages.error(request, "Неправильний формат JSON!")
            return redirect("custom_admin:add_channel")

    # Render the form if it's a GET request
    return render(request, "custom_admin/add_channel.html")
