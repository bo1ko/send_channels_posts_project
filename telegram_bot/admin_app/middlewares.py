import logging

from typing import Callable, Any, Dict, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import (
    TelegramObject,
)

from admin_app.db_requests import get_or_create_user

logger = logging.getLogger(__name__)


class CheckAndAddUserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        """
        A middleware that checks if user is in database and adds it if not.

        Args:
            handler: a callable that takes TelegramObject and Dict[str, Any] and returns Awaitable[Any]
            event: a TelegramObject
            data: a Dict[str, Any]

        Returns:
            Awaitable[Any]
        """

        try:
            user, created = await get_or_create_user(event.from_user.id)

            if created:
                logger.info(f"User added to database {user.telegram_id}")
        except Exception as e:
            logger.error("CheckAndAddUserMiddleware error")
            logger.error(f"{e.with_traceback}")

        return await handler(event, data)
