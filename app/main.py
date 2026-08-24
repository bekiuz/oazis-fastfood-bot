from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import Settings
from app.database.client import create_supabase_client
from app.database.repository import Repository
from app.handlers.admin import create_admin_router
from app.handlers.user import create_user_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger(__name__)


async def main() -> None:
    settings = Settings.from_env()
    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dispatcher = Dispatcher(storage=MemoryStorage())
    repository = Repository(create_supabase_client(settings))
    dispatcher.include_router(create_admin_router(repository, settings))
    dispatcher.include_router(create_user_router(repository, settings))

    try:
        bot_info = await bot.get_me()
        logger.info("Starting @%s", bot_info.username)
        await dispatcher.start_polling(bot, allowed_updates=dispatcher.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped")
