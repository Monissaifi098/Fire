from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from loguru import logger

from config import config
from database import get_or_create_user, get_user, claim_daily_bonus, update_user_rank, get_user_referrals
from keyboards import main_menu_kb, back_to_main_kb, vip_kb
from utils.messages import (
    welcome_message, account_message, referral_message, vip_message,
    format_currency
)

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    args = message.text.split()
    referred_by = None

    if len(args) > 1 and args[1].startswith("ref_"):
        ref_code = args[1][4:]
        from database.db import get_session
        from sqlalchemy import select
        from database.models import User
        async with get_session() as session:
            result = await session.execute(select(User).where(User.referral_code == ref_code))
            ref_user = result.scalar_one_or_none()
            if ref_user and ref_user.telegram_id != message.from_user.id:
                referred_by = ref_user.telegram_id

    user = await get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
        referred_by=referred_by,
    )
    await update_user_rank(message.from_user.id)

    is_new = user.total_orders == 0 and user.balance == 0.0
    text = welcome_message(message.from_user.first_name, is_new=is_new)

    if referred_by:
        text += f"\n\n🎉 <b>Referral bonus applied!</b> Welcome gift credited."

    await message.answer(text, reply_markup=main_menu_kb(), parse_mode="HTML")


@router.callback_query(F.data == "menu_main")
async def cb_main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user = await get_user(callback.from_user.id)
    if not user:
        await callback.answer("Please use /start first", show_alert=True)
        return
    text = welcome_message(callback.from_user.first_name)
    await callback.message.edit_text(text, reply_markup=main_menu_kb(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "menu_account")
async def cb_account(callback: CallbackQuery):
    user = await get_user(callback.from_user.id)
    if not user:
        await callback.answer("Please use /start first", show_alert=True)
        return
    await update_user_rank(callback.from_user.id)
    user = await get_user(callback.from_user.id)
    text = account_message(user)
    await callback.message.edit_text(text, reply_markup=back_to_main_kb(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "menu_daily_bonus")
async def cb_daily_bonus(callback: CallbackQuery):
    success, bonus = await claim_daily_bonus(callback.from_user.id)
    if success:
        user = await get_user(callback.from_user.id)
        text = (
            "🎉 <b>DAILY BONUS CLAIMED!</b>\n\n"
            f"💰 <b>Bonus Received:</b> {format_currency(bonus)}\n"
            f"💳 <b>New Balance:</b> {format_currency(user.balance)}\n\n"
            "⏰ Come back in 24 hours for your next bonus!\n"
            + ("👑 <b>VIP Bonus:</b> You earned 2x bonus!" if user.is_vip else "")
        )
        await callback.message.edit_text(text, reply_markup=back_to_main_kb(), parse_mode="HTML")
        await callback.answer("🎉 Bonus claimed!", show_alert=True)
    else:
        user = await get_user(callback.from_user.id)
        from datetime import datetime, timezone
        if user.daily_bonus_claimed:
            remaining = 86400 - (datetime.utcnow() - user.daily_bonus_claimed).total_seconds()
            hours = int(remaining // 3600)
            minutes = int((remaining % 3600) // 60)
            text = (
                f"⏰ <b>Already claimed today!</b>\n\n"
                f"⌛ Come back in <b>{hours}h {minutes}m</b>\n\n"
                f"💰 Daily bonus: {format_currency(config.DAILY_BONUS)}\n"
                f"👑 VIP bonus: {format_currency(config.DAILY_BONUS * 2)} (2x)"
            )
        else:
            text = "Something went wrong. Try again."
        await callback.message.edit_text(text, reply_markup=back_to_main_kb(), parse_mode="HTML")
        await callback.answer("Already claimed today!", show_alert=True)


@router.callback_query(F.data == "menu_referral")
async def cb_referral(callback: CallbackQuery):
    user = await get_user(callback.from_user.id)
    if not user:
        await callback.answer()
        return
    referrals = await get_user_referrals(callback.from_user.id)
    text = referral_message(user)
    text += f"\n\n👥 <b>Total Referrals:</b> {len(referrals)}"

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    bot_link = f"https://t.me/{config.BOT_USERNAME}?start=ref_{user.referral_code}"
    builder.row(InlineKeyboardButton(text="📤 Share Referral Link", url=f"https://t.me/share/url?url={bot_link}&text=🔥 Join Fire Service - Premium SMM Panel!"))
    builder.row(InlineKeyboardButton(text="🏠 Main Menu", callback_data="menu_main"))

    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "menu_vip")
async def cb_vip(callback: CallbackQuery):
    user = await get_user(callback.from_user.id)
    text = vip_message()
    if user and user.is_vip:
        text = "👑 <b>You are already a VIP member!</b>\n\n" + text
    await callback.message.edit_text(text, reply_markup=vip_kb(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.in_(["vip_monthly", "vip_yearly"]))
async def cb_vip_purchase(callback: CallbackQuery):
    plan = "Monthly" if callback.data == "vip_monthly" else "Yearly"
    price = config.VIP_PRICE_MONTHLY if callback.data == "vip_monthly" else config.VIP_PRICE_YEARLY
    user = await get_user(callback.from_user.id)

    if not user:
        await callback.answer()
        return

    if user.balance < price:
        shortage = price - user.balance
        text = (
            f"❌ <b>Insufficient Balance!</b>\n\n"
            f"💰 <b>Required:</b> {format_currency(price)}\n"
            f"💳 <b>Your Balance:</b> {format_currency(user.balance)}\n"
            f"📉 <b>Shortage:</b> {format_currency(shortage)}\n\n"
            "➕ Please add funds first!"
        )
        from keyboards import add_funds_kb
        await callback.message.edit_text(text, reply_markup=add_funds_kb(), parse_mode="HTML")
        await callback.answer("Insufficient balance!", show_alert=True)
        return

    # Deduct and grant VIP
    from database.db import get_session
    from sqlalchemy import update
    from database.models import User
    from datetime import datetime, timedelta

    async with get_session() as session:
        duration = timedelta(days=30 if plan == "Monthly" else 365)
        expires = datetime.utcnow() + duration
        await session.execute(
            update(User).where(User.telegram_id == callback.from_user.id)
            .values(balance=User.balance - price, is_vip=True, vip_expires=expires)
        )

    text = (
        f"👑 <b>VIP ACTIVATED!</b>\n\n"
        f"🎉 Welcome to the elite club!\n\n"
        f"📦 <b>Plan:</b> {plan} VIP\n"
        f"💰 <b>Amount Paid:</b> {format_currency(price)}\n"
        f"⏰ <b>Valid Until:</b> {(datetime.utcnow() + (timedelta(days=30) if plan == 'Monthly' else timedelta(days=365))).strftime('%d %b %Y')}\n\n"
        "✅ <b>Benefits now active:</b>\n"
        "• 15% off all orders\n"
        "• 2x daily bonus\n"
        "• Priority support"
    )
    await callback.message.edit_text(text, reply_markup=back_to_main_kb(), parse_mode="HTML")
    await callback.answer("👑 VIP Activated!", show_alert=True)


@router.callback_query(F.data == "menu_help")
async def cb_help(callback: CallbackQuery):
    text = (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "ℹ️  <b>HELP & FAQ</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>🛒 How to Order?</b>\n"
        "1. Go to 🛒 Order Services\n"
        "2. Select a category (Instagram, YouTube, etc.)\n"
        "3. Choose the service you want\n"
        "4. Enter your profile/post link\n"
        "5. Enter quantity & confirm!\n\n"
        "<b>💳 How to Add Funds?</b>\n"
        "1. Click 💳 Add Funds\n"
        "2. Select or enter amount\n"
        "3. Pay via UPI\n"
        "4. Submit screenshot\n"
        "5. Admin verifies & credits!\n\n"
        "<b>📦 Order Statuses:</b>\n"
        "⏳ Pending — Waiting to start\n"
        "🔄 Processing — Being submitted\n"
        "▶️ In Progress — Running\n"
        "✅ Completed — Done!\n"
        "⚠️ Partial — Partially done\n\n"
        f"<b>💬 Support:</b> {config.SUPPORT_USERNAME}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    await callback.message.edit_text(text, reply_markup=back_to_main_kb(), parse_mode="HTML")
    await callback.answer()
