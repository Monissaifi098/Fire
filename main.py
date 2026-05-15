import asyncio
import logging
from loguru import logger
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from config import config
from database import init_db
from handlers import start_router, orders_router, payments_router, support_router, admin_router
from middlewares import RateLimitMiddleware, BanCheckMiddleware


async def on_startup(bot: Bot):
    logger.info("🔥 Fire Service Bot starting up...")
    await init_db()
    logger.info(f"🤖 Bot: {config.BOT_NAME}")
    logger.info(f"👮 Admins: {config.ADMIN_IDS}")

    for admin_id in config.ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                "🔥 <b>Fire Service Bot is ONLINE!</b>\n\n"
                "✅ Database initialized\n"
                "✅ All handlers loaded\n"
                "✅ Ready to accept orders\n\n"
                "Use /admin to open the admin panel.",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.warning(f"Could not notify admin {admin_id}: {e}")

    logger.success("✅ Bot started successfully!")


async def on_shutdown(bot: Bot):
    logger.info("🛑 Bot shutting down...")


async def main():
    logging.basicConfig(level=logging.WARNING)

    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    dp = Dispatcher(storage=MemoryStorage())

    # Register middlewares
    dp.message.middleware(RateLimitMiddleware())
    dp.message.middleware(BanCheckMiddleware())
    dp.callback_query.middleware(BanCheckMiddleware())

    # Register routers (order matters)
    dp.include_router(admin_router)
    dp.include_router(start_router)
    dp.include_router(orders_router)
    dp.include_router(payments_router)
    dp.include_router(support_router)

    # Startup / shutdown hooks
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    logger.info("🚀 Starting polling...")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
