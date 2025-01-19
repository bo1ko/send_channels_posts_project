from typing import Callable, Any, Dict, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import (
    TelegramObject,
)

from telegram_bot.core.db_request import get_or_create_user

class CheckAndAddUserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        try:
            user, created = await get_or_create_user(
                event.from_user.id, event.from_user.username
            )
        except Exception as e:
            print(e)

        return await handler(event, data)