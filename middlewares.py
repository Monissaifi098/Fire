from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from typing import Callable, Awaitable, Any
from collections import defaultdict
from datetime import datetime, timedelta
from config import config
from loguru import logger


class RateLimitMiddleware(BaseMiddleware):
    def __init__(self):
        self.user_messages: dict = defaultdict(list)
        self.banned_until: dict = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict], Awaitable[Any]],
        event: TelegramObject,
        data: dict,
    ) -> Any:
        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id

        if user_id:
            now = datetime.now()

            # Check if temporarily banned
            if user_id in self.banned_until:
                if now < self.banned_until[user_id]:
                    if isinstance(event, Message):
                        await event.answer("⚠️ Slow down! You're sending too many requests. Please wait a moment.")
                    elif isinstance(event, CallbackQuery):
                        await event.answer("⚠️ Too fast! Please wait a moment.", show_alert=True)
                    return
                else:
                    del self.banned_until[user_id]

            # Clean old messages
            period = timedelta(seconds=config.RATE_LIMIT_PERIOD)
            self.user_messages[user_id] = [
                t for t in self.user_messages[user_id] if now - t < period
            ]

            # Check rate limit
            self.user_messages[user_id].append(now)
            if len(self.user_messages[user_id]) > config.RATE_LIMIT_MESSAGES:
                self.banned_until[user_id] = now + timedelta(seconds=30)
                logger.warning(f"Rate limit triggered for user {user_id}")
                if isinstance(event, Message):
                    await event.answer("🔥 Too many requests! You've been temporarily rate-limited for 30 seconds.")
                elif isinstance(event, CallbackQuery):
                    await event.answer("🔥 Slow down! Rate limited for 30s.", show_alert=True)
                return

        return await handler(event, data)


class BanCheckMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict], Awaitable[Any]],
        event: TelegramObject,
        data: dict,
    ) -> Any:
        from database import get_user

        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id

        if user_id:
            from config import config as cfg
            if user_id not in cfg.ADMIN_IDS:
                user = await get_user(user_id)
                if user and user.is_banned:
                    reason = user.ban_reason or "Violation of terms"
                    text = f"🚫 <b>Your account has been banned.</b>\n\nReason: {reason}\n\nContact support if you think this is a mistake."
                    if isinstance(event, Message):
                        await event.answer(text, parse_mode="HTML")
                    elif isinstance(event, CallbackQuery):
                        await event.answer("🚫 Your account is banned.", show_alert=True)
                    return

        return await handler(event, data)
