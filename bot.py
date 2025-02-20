from __future__ import annotations

from dataclasses import dataclass

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.redis import RedisStorage
from aiogram_tonconnect.handlers import AiogramTonConnectHandlers
from aiogram_tonconnect.middleware import AiogramTonConnectMiddleware
from aiogram_tonconnect.tonconnect.storage import ATCRedisStorage
from aiogram_tonconnect.utils.qrcode import QRUrlProvider
from environs import Env
from tonutils.tonconnect import TonConnect

from handlers import router
from throttling import ThrottlingMiddleware


@dataclass
class Config:
    BOT_TOKEN: str
    REDIS_DSN: str
    MANIFEST_URL: str

    @classmethod
    def load(cls) -> Config:
        env = Env()
        env.read_env()

        return cls(
            BOT_TOKEN=env.str("BOT_TOKEN"),
            REDIS_DSN=env.str("REDIS_DSN"),
            MANIFEST_URL=env.str("MANIFEST_URL"),
        )


async def main():

    config = Config.load()

    storage = RedisStorage.from_url(config.REDIS_DSN)
    bot = Bot(config.BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher(storage=storage)

    dp.update.middleware.register(ThrottlingMiddleware())

    tonconnect = TonConnect(
        manifest_url=config.MANIFEST_URL,
        storage=ATCRedisStorage(storage.redis),
    )
    dp.update.middleware.register(
        AiogramTonConnectMiddleware(
            tonconnect=tonconnect,
            qrcode_provider=QRUrlProvider(),
        )
    )

    AiogramTonConnectHandlers().register(dp)

    dp.include_router(router)

    await dp.start_polling(bot)


if __name__ == '__main__':
    import asyncio

    asyncio.run(main())
