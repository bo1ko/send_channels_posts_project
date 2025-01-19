from aiogram.filters import Filter
from aiogram import types, Bot

from telegram_bot.admin_app.db_requests import is_user_admin


class IsAdmin(Filter):
    def __init__(self) -> None:
        pass

    async def __call__(self, message: types.Message, bot: Bot) -> bool:
        return await is_user_admin(message.from_user.id)
