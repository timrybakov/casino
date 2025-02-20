from typing import Any, Awaitable, Callable, Dict, MutableMapping, Optional

from aiogram import BaseMiddleware
from aiogram.dispatcher.flags import get_flag
from aiogram.types import TelegramObject, User
from cachetools import TTLCache


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(
        self,
        *,
        default_key: Optional[str] = "default",
        default_ttl: float = 0.7,
        **ttl_map: float,
    ) -> None:
        if default_key:
            ttl_map[default_key] = default_ttl
        self.default_key = default_key
        self.caches: Dict[str, MutableMapping[int, None]] = {
            name: TTLCache(maxsize=10_000, ttl=ttl)
            for name, ttl in ttl_map.items()
        }

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Optional[Any]:

        user: Optional[User] = data.get("event_from_user")
        if user:
            throttling_key = get_flag(data, "throttling_key", default=self.default_key)
            if throttling_key and user.id in self.caches[throttling_key]:
                return None
            self.caches[throttling_key][user.id] = None

        return await handler(event, data)