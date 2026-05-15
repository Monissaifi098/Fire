from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from loguru import logger
from datetime import datetime, timedelta

from config import config
from database import (
    get_user, get_all_users, get_user_count, update_user_balance,
    ban_user, unban_user, get_stats,
    get_all_categories, get_all_services, get_service, get_category,
    create_category, create_service, update_service, delete_service,
    get_pending_payments, get_payment, approve_payment, reject_payment,
    get_all_orders, get_order, update_order_status,
    get_open_tickets, get_ticket, reply_ticket, close_ticket,
    get_all_coupons, create_coupon,
)
from keyboards import (
    admin_main_kb, admin_users_kb, admin_services_kb, admin_payments_kb,
    payment_action_kb, admin_orders_kb, admin_tickets_kb, ticket_action_kb,
    admin_coupons_kb, admin_settings_kb, admin_categories_select_kb,
    confirm_broadcast_kb, cancel_kb, back_to_main_kb,
)
from states import AdminStates
from utils.messages import stats_message, format_currency, get_status_text, format_number

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in config.ADMIN_IDS


# ─────────────────────────────────────────────
# ADMIN ENTRY
# ─────────────────────────────────────────────

@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Access denied.")
        return
    await state.clear()
    text = (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🛡️  <b>ADMIN PANEL</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👋 Welcome, Admin!\n"
        f"🤖 <b>Bot:</b> {config.BOT_NAME}\n\n"
        "Select an option:"
    )
    await message.answer(text, reply_markup=admin_main_kb(), parse_mode="HTML")


@router.callback_query(F.data == "adm_main")
async def cb_admin_main(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Access denied.", show_alert=True)
        return
    await state.clear()
    text = (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🛡️  <b>ADMIN PANEL</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Select an option:"
    )
    await callback.message.edit_text(text, reply_markup=admin_main_kb(), parse_mode="HTML")
    await callback.answer()


# ─────────────────────────────────────────────
# STATS
# ─────────────────────────────────────────────

@router.message(Command("stats"))
@router.callback_query(F.data == "adm_stats")
async def cb_admin_stats(event, state: FSMContext = None):
    if isinstance(event, Message):
        if not is_admin(event.from_user.id): return
        stats = await get_stats()
        await event.answer(stats_message(stats), reply_markup=admin_main_kb(), parse_mode="HTML")
    else:
        if not is_admin(event.from_user.id):
            await event.answer("⛔", show_alert=True); return
        stats = await get_stats()
        await event.message.edit_text(stats_message(stats), reply_markup=admin_main_kb(), parse_mode="HTML")
        await event.answer()


# ─────────────────────────────────────────────
# USER MANAGEMENT
# ─────────────────────────────────────────────

@router.message(Command("users"))
@router.callback_query(F.data == "adm_users")
async def cb_admin_users(event, state: FSMContext = None):
    if isinstance(event, Message):
        if not is_admin(event.from_user.id): return
        count = await get_user_count()
        text = f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n👥  <b>USER MANAGEMENT</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n📊 <b>Total Users:</b> {count}\n\nSelect action:"
        await event.answer(text, reply_markup=admin_users_kb(), parse_mode="HTML")
    else:
        if not is_admin(event.from_user.id):
            await event.answer("⛔", show_alert=True); return
        count = await get_user_count()
        text = f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n👥  <b>USER MANAGEMENT</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n📊 <b>Total Users:</b> {count}\n\nSelect action:"
        await event.message.edit_text(text, reply_markup=admin_users_kb(), parse_mode="HTML")
        await event.answer()


@router.callback_query(F.data == "adm_find_user")
async def cb_find_user(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    await state.set_state(AdminStates.find_user)
    await callback.message.edit_text("🔍 <b>FIND USER</b>\n\nEnter User ID or @username:", reply_markup=cancel_kb(), parse_mode="HTML")
    await callback.answer()


@router.message(AdminStates.find_user)
async def process_find_user(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    query = message.text.strip().lstrip("@")
    user = None
    try:
        uid = int(query)
        user = await get_user(uid)
    except ValueError:
        users = await get_all_users()
        for u in users:
            if u.username and u.username.lower() == query.lower():
                user = u
                break

    await state.clear()
    if not user:
        await message.answer("❌ User not found.", reply_markup=admin_main_kb(), parse_mode="HTML")
        return

    text = (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤  <b>USER INFO</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🆔 <b>ID:</b> <code>{user.telegram_id}</code>\n"
        f"👤 <b>Name:</b> {user.full_name or 'N/A'}\n"
        f"📛 <b>Username:</b> @{user.username or 'N/A'}\n\n"
        f"💰 <b>Balance:</b> {format_currency(user.balance)}\n"
        f"📊 <b>Total Spent:</b> {format_currency(user.total_spent)}\n"
        f"💳 <b>Total Deposited:</b> {format_currency(user.total_deposited)}\n\n"
        f"📦 <b>Orders:</b> {user.total_orders}\n"
        f"🏆 <b>Rank:</b> {user.rank}\n"
        f"👑 <b>VIP:</b> {'Yes' if user.is_vip else 'No'}\n"
        f"🚫 <b>Banned:</b> {'Yes — ' + (user.ban_reason or '') if user.is_banned else 'No'}\n"
        f"📅 <b>Joined:</b> {user.created_at.strftime('%d %b %Y')}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💰 Add Balance", callback_data=f"adm_addbal_{user.telegram_id}"),
        InlineKeyboardButton(text="🚫 Ban", callback_data=f"adm_doban_{user.telegram_id}"),
    )
    builder.row(
        InlineKeyboardButton(text="✅ Unban", callback_data=f"adm_dounban_{user.telegram_id}"),
        InlineKeyboardButton(text="👑 Grant VIP", callback_data=f"adm_givevip_{user.telegram_id}"),
    )
    builder.row(InlineKeyboardButton(text="◀️ Back", callback_data="adm_users"))
    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")


@router.callback_query(F.data == "adm_add_balance")
async def cb_add_balance_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    await state.set_state(AdminStates.add_balance_user_id)
    await callback.message.edit_text("💰 <b>ADD BALANCE</b>\n\nEnter User ID:", reply_markup=cancel_kb(), parse_mode="HTML")
    await callback.answer()


@router.message(AdminStates.add_balance_user_id)
async def process_add_balance_uid(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    try:
        uid = int(message.text.strip())
        user = await get_user(uid)
        if not user:
            await message.answer("❌ User not found.")
            return
        await state.update_data(target_uid=uid, target_name=user.full_name)
        await state.set_state(AdminStates.add_balance_amount)
        await message.answer(f"✅ User: <b>{user.full_name}</b>\n\nEnter amount to add (₹):", reply_markup=cancel_kb(), parse_mode="HTML")
    except ValueError:
        await message.answer("❌ Invalid User ID.")


@router.message(AdminStates.add_balance_amount)
async def process_add_balance_amount(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    try:
        amount = float(message.text.strip().replace(",", ""))
        data = await state.get_data()
        await update_user_balance(data["target_uid"], amount)
        await state.clear()
        # Notify user
        try:
            await message.bot.send_message(
                data["target_uid"],
                f"💰 <b>Balance Added!</b>\n\n✅ {format_currency(amount)} has been added to your account by admin.",
                parse_mode="HTML"
            )
        except: pass
        await message.answer(
            f"✅ <b>Balance Added!</b>\n\n👤 User: {data['target_name']}\n💰 Amount: {format_currency(amount)}",
            reply_markup=admin_main_kb(), parse_mode="HTML"
        )
    except ValueError:
        await message.answer("❌ Invalid amount.")


@router.callback_query(F.data.startswith("adm_addbal_"))
async def cb_addbal_quick(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    uid = int(callback.data.split("_")[-1])
    user = await get_user(uid)
    await state.update_data(target_uid=uid, target_name=user.full_name if user else str(uid))
    await state.set_state(AdminStates.add_balance_amount)
    await callback.message.answer(f"💰 Add balance to <b>{user.full_name if user else uid}</b>\n\nEnter amount:", reply_markup=cancel_kb(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "adm_ban_user")
async def cb_ban_user_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    await state.set_state(AdminStates.ban_user_id)
    await callback.message.edit_text("🚫 <b>BAN USER</b>\n\nEnter User ID:", reply_markup=cancel_kb(), parse_mode="HTML")
    await callback.answer()


@router.message(AdminStates.ban_user_id)
async def process_ban_uid(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    try:
        uid = int(message.text.strip())
        await state.update_data(ban_uid=uid)
        await state.set_state(AdminStates.ban_reason)
        await message.answer("Enter ban reason:", reply_markup=cancel_kb())
    except ValueError:
        await message.answer("❌ Invalid User ID.")


@router.message(AdminStates.ban_reason)
async def process_ban_reason(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    data = await state.get_data()
    await ban_user(data["ban_uid"], message.text.strip())
    await state.clear()
    try:
        await message.bot.send_message(data["ban_uid"], f"🚫 <b>Your account has been banned.</b>\n\nReason: {message.text.strip()}", parse_mode="HTML")
    except: pass
    await message.answer(f"✅ User <code>{data['ban_uid']}</code> banned.", reply_markup=admin_main_kb(), parse_mode="HTML")


@router.callback_query(F.data.startswith("adm_doban_"))
async def cb_doban(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    uid = int(callback.data.split("_")[-1])
    await state.update_data(ban_uid=uid)
    await state.set_state(AdminStates.ban_reason)
    await callback.message.answer(f"Enter ban reason for <code>{uid}</code>:", reply_markup=cancel_kb(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "adm_unban_user")
async def cb_unban_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    await state.set_state(AdminStates.ban_user_id)
    await callback.message.edit_text("✅ <b>UNBAN USER</b>\n\nEnter User ID:", reply_markup=cancel_kb(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("adm_dounban_"))
async def cb_dounban(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    uid = int(callback.data.split("_")[-1])
    await unban_user(uid)
    try:
        await callback.bot.send_message(uid, "✅ <b>Your account has been unbanned!</b>", parse_mode="HTML")
    except: pass
    await callback.answer("✅ User unbanned!", show_alert=True)


@router.callback_query(F.data.startswith("adm_givevip_"))
async def cb_give_vip(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    uid = int(callback.data.split("_")[-1])
    from database.db import get_session
    from sqlalchemy import update
    from database.models import User
    async with get_session() as session:
        expires = datetime.utcnow() + timedelta(days=30)
        await session.execute(update(User).where(User.telegram_id == uid).values(is_vip=True, vip_expires=expires))
    try:
        await callback.bot.send_message(uid, "👑 <b>VIP status granted by admin!</b>\nYou now have 30 days of VIP benefits.", parse_mode="HTML")
    except: pass
    await callback.answer("👑 VIP granted!", show_alert=True)


@router.callback_query(F.data == "adm_grant_vip")
async def cb_grant_vip_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    await state.set_state(AdminStates.find_user)
    await callback.message.edit_text("👑 Enter User ID to grant VIP:", reply_markup=cancel_kb(), parse_mode="HTML")
    await callback.answer()


# ─────────────────────────────────────────────
# SERVICES MANAGEMENT
# ─────────────────────────────────────────────

@router.message(Command("services"))
@router.callback_query(F.data == "adm_services")
async def cb_admin_services(event, state: FSMContext = None):
    if isinstance(event, Message):
        if not is_admin(event.from_user.id): return
        await event.answer("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n📦  <b>SERVICES MANAGEMENT</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", reply_markup=admin_services_kb(), parse_mode="HTML")
    else:
        if not is_admin(event.from_user.id): return
        await event.message.edit_text("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n📦  <b>SERVICES MANAGEMENT</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", reply_markup=admin_services_kb(), parse_mode="HTML")
        await event.answer()


@router.callback_query(F.data == "adm_add_category")
async def cb_add_cat(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    await state.set_state(AdminStates.add_category_name)
    await callback.message.edit_text("➕ <b>ADD CATEGORY</b>\n\nEnter category name:", reply_markup=cancel_kb(), parse_mode="HTML")
    await callback.answer()


@router.message(AdminStates.add_category_name)
async def process_cat_name(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    await state.update_data(cat_name=message.text.strip())
    await state.set_state(AdminStates.add_category_emoji)
    await message.answer("Enter category emoji (e.g. 📸):")


@router.message(AdminStates.add_category_emoji)
async def process_cat_emoji(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    await state.update_data(cat_emoji=message.text.strip())
    await state.set_state(AdminStates.add_category_desc)
    await message.answer("Enter description (or send '-' to skip):")


@router.message(AdminStates.add_category_desc)
async def process_cat_desc(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    data = await state.get_data()
    desc = "" if message.text.strip() == "-" else message.text.strip()
    cat = await create_category(data["cat_name"], data["cat_emoji"], desc)
    await state.clear()
    await message.answer(f"✅ Category <b>{cat.emoji} {cat.name}</b> created! ID: {cat.id}", reply_markup=admin_services_kb(), parse_mode="HTML")


@router.callback_query(F.data == "adm_add_service")
async def cb_add_service(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    cats = await get_all_categories()
    await state.set_state(AdminStates.add_service_category)
    await callback.message.edit_text("➕ <b>ADD SERVICE</b>\n\nSelect category:", reply_markup=admin_categories_select_kb(cats), parse_mode="HTML")
    await callback.answer()


@router.callback_query(AdminStates.add_service_category, F.data.startswith("adm_selcat_"))
async def process_svc_cat(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    cat_id = int(callback.data.split("_")[-1])
    await state.update_data(svc_cat_id=cat_id)
    await state.set_state(AdminStates.add_service_name)
    await callback.message.edit_text("Enter service name:", reply_markup=cancel_kb(), parse_mode="HTML")
    await callback.answer()


@router.message(AdminStates.add_service_name)
async def process_svc_name(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    await state.update_data(svc_name=message.text.strip())
    await state.set_state(AdminStates.add_service_price)
    await message.answer("Enter price per 1000 (in ₹):")


@router.message(AdminStates.add_service_price)
async def process_svc_price(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    try:
        price = float(message.text.strip())
        await state.update_data(svc_price=price)
        await state.set_state(AdminStates.add_service_min)
        await message.answer("Enter minimum quantity:")
    except ValueError:
        await message.answer("❌ Invalid price.")


@router.message(AdminStates.add_service_min)
async def process_svc_min(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    try:
        await state.update_data(svc_min=int(message.text.strip()))
        await state.set_state(AdminStates.add_service_max)
        await message.answer("Enter maximum quantity:")
    except ValueError:
        await message.answer("❌ Invalid number.")


@router.message(AdminStates.add_service_max)
async def process_svc_max(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    try:
        await state.update_data(svc_max=int(message.text.strip()))
        await state.set_state(AdminStates.add_service_api_id)
        await message.answer("Enter SMM API Service ID (or '-' to skip):")
    except ValueError:
        await message.answer("❌ Invalid number.")


@router.message(AdminStates.add_service_api_id)
async def process_svc_api_id(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    api_id = "" if message.text.strip() == "-" else message.text.strip()
    await state.update_data(svc_api_id=api_id)
    await state.set_state(AdminStates.add_service_time)
    await message.answer("Enter average delivery time (e.g. '0-24 hours'):")


@router.message(AdminStates.add_service_time)
async def process_svc_time(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    data = await state.get_data()
    svc = await create_service(
        category_id=data["svc_cat_id"], name=data["svc_name"],
        price_per_1000=data["svc_price"], min_qty=data["svc_min"],
        max_qty=data["svc_max"], api_service_id=data.get("svc_api_id", ""),
        avg_time=message.text.strip()
    )
    await state.clear()
    await message.answer(
        f"✅ Service created!\n\n🆔 ID: {svc.id}\n📦 Name: {svc.name}\n💰 Price: {format_currency(svc.price_per_1000)}/1K",
        reply_markup=admin_services_kb(), parse_mode="HTML"
    )


@router.callback_query(F.data == "adm_list_services")
async def cb_list_services(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    services = await get_all_services()
    if not services:
        await callback.answer("No services found.", show_alert=True)
        return
    lines = []
    for svc in services[:20]:
        status = "✅" if svc.is_active else "❌"
        lines.append(f"{status} <b>#{svc.id}</b> {svc.name[:30]}\n   💰 {format_currency(svc.price_per_1000)}/1K | Min:{format_number(svc.min_quantity)}")
    text = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n📦 <b>ALL SERVICES</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n" + "\n\n".join(lines)
    await callback.message.edit_text(text, reply_markup=admin_services_kb(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "adm_delete_service")
async def cb_delete_service_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    await state.set_state(AdminStates.edit_service_field)
    await state.update_data(action="delete")
    await callback.message.edit_text("🗑️ Enter Service ID to delete:", reply_markup=cancel_kb(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "adm_edit_service")
async def cb_edit_service_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    await state.set_state(AdminStates.edit_service_field)
    await state.update_data(action="edit")
    await callback.message.edit_text("✏️ Enter Service ID to edit:", reply_markup=cancel_kb(), parse_mode="HTML")
    await callback.answer()


@router.message(AdminStates.edit_service_field)
async def process_edit_svc_id(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    data = await state.get_data()
    try:
        svc_id = int(message.text.strip())
        svc = await get_service(svc_id)
        if not svc:
            await message.answer("❌ Service not found.")
            return
        if data.get("action") == "delete":
            await delete_service(svc_id)
            await state.clear()
            await message.answer(f"✅ Service #{svc_id} deleted.", reply_markup=admin_services_kb(), parse_mode="HTML")
        else:
            await state.update_data(edit_svc_id=svc_id)
            await state.set_state(AdminStates.edit_service_value)
            await message.answer(
                f"Current: <b>{svc.name}</b>\nPrice: {format_currency(svc.price_per_1000)}/1K\n\nSend new price per 1000:",
                parse_mode="HTML"
            )
    except ValueError:
        await message.answer("❌ Invalid ID.")


@router.message(AdminStates.edit_service_value)
async def process_edit_svc_value(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    try:
        new_price = float(message.text.strip())
        data = await state.get_data()
        await update_service(data["edit_svc_id"], price_per_1000=new_price)
        await state.clear()
        await message.answer(f"✅ Service price updated to {format_currency(new_price)}/1K", reply_markup=admin_services_kb(), parse_mode="HTML")
    except ValueError:
        await message.answer("❌ Invalid price.")


# ─────────────────────────────────────────────
# PAYMENT MANAGEMENT
# ─────────────────────────────────────────────

@router.message(Command("payments"))
@router.callback_query(F.data == "adm_payments")
async def cb_admin_payments(event, state: FSMContext = None):
    if isinstance(event, Message):
        if not is_admin(event.from_user.id): return
        await event.answer("💳 <b>PAYMENT MANAGEMENT</b>", reply_markup=admin_payments_kb(), parse_mode="HTML")
    else:
        if not is_admin(event.from_user.id): return
        await event.message.edit_text("💳 <b>PAYMENT MANAGEMENT</b>", reply_markup=admin_payments_kb(), parse_mode="HTML")
        await event.answer()


@router.callback_query(F.data == "adm_pending_payments")
async def cb_pending_payments(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    payments = await get_pending_payments()
    if not payments:
        await callback.message.edit_text("✅ No pending payments!", reply_markup=admin_payments_kb(), parse_mode="HTML")
        await callback.answer()
        return
    for p in payments[:5]:
        user = await get_user(p.user_id)
        text = (
            f"💳 <b>Payment #{p.id}</b>\n"
            f"👤 {user.full_name if user else p.user_id} (<code>{p.user_id}</code>)\n"
            f"💰 {format_currency(p.amount)}\n"
            f"🔖 TXN: {p.transaction_id or 'Screenshot attached'}\n"
            f"📅 {p.created_at.strftime('%d %b %Y, %I:%M %p')}"
        )
        if p.screenshot_file_id:
            await callback.bot.send_photo(callback.from_user.id, p.screenshot_file_id, caption=text, reply_markup=payment_action_kb(p.id), parse_mode="HTML")
        else:
            await callback.bot.send_message(callback.from_user.id, text, reply_markup=payment_action_kb(p.id), parse_mode="HTML")
    await callback.answer(f"📋 Showing {len(payments)} pending payment(s)")


@router.callback_query(F.data.startswith("adm_pay_approve_"))
async def cb_approve_payment(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    payment_id = int(callback.data.split("_")[-1])
    success = await approve_payment(payment_id, callback.from_user.id)
    if not success:
        await callback.answer("❌ Payment already processed.", show_alert=True)
        return
    payment = await get_payment(payment_id)
    user = await get_user(payment.user_id)
    # Notify user
    try:
        await callback.bot.send_message(
            payment.user_id,
            f"✅ <b>Payment Approved!</b>\n\n💰 {format_currency(payment.amount)} has been added to your balance!\n🆔 Payment #{payment_id}",
            parse_mode="HTML"
        )
    except: pass
    await callback.answer(f"✅ Payment #{payment_id} approved!", show_alert=True)
    await callback.message.edit_caption(
        callback.message.caption + "\n\n✅ <b>APPROVED</b>",
        reply_markup=None, parse_mode="HTML"
    ) if callback.message.caption else await callback.message.edit_text(
        callback.message.text + "\n\n✅ <b>APPROVED</b>", reply_markup=None, parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("adm_pay_reject_"))
async def cb_reject_payment(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    payment_id = int(callback.data.split("_")[-1])
    await reject_payment(payment_id, callback.from_user.id, "Rejected by admin")
    payment = await get_payment(payment_id)
    try:
        await callback.bot.send_message(
            payment.user_id,
            f"❌ <b>Payment Rejected!</b>\n\n🆔 Payment #{payment_id}\n💰 {format_currency(payment.amount)}\n\nIf this is a mistake, please contact support.",
            parse_mode="HTML"
        )
    except: pass
    await callback.answer(f"❌ Payment #{payment_id} rejected!", show_alert=True)


# ─────────────────────────────────────────────
# ORDER MANAGEMENT
# ─────────────────────────────────────────────

@router.callback_query(F.data == "adm_orders")
async def cb_admin_orders(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    await callback.message.edit_text("📝 <b>ORDER MANAGEMENT</b>", reply_markup=admin_orders_kb(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "adm_recent_orders")
async def cb_recent_orders(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    orders = await get_all_orders(limit=10)
    if not orders:
        await callback.answer("No orders found.", show_alert=True)
        return
    lines = []
    for o in orders:
        lines.append(f"<b>#{o.id}</b> {get_status_text(o.status)} | {o.service_name[:25]}\n👤 {o.user_id} | 💰{format_currency(o.price)}")
    text = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n📝 <b>RECENT ORDERS</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n" + "\n\n".join(lines)
    await callback.message.edit_text(text, reply_markup=admin_orders_kb(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.in_(["adm_search_order", "adm_force_complete", "adm_force_cancel"]))
async def cb_order_action(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    action = {"adm_search_order": "search", "adm_force_complete": "complete", "adm_force_cancel": "cancel"}[callback.data]
    await state.update_data(order_action=action)
    await state.set_state(AdminStates.order_id_input)
    prompts = {"search": "🔍 Enter Order ID:", "complete": "✅ Enter Order ID to force complete:", "cancel": "❌ Enter Order ID to force cancel:"}
    await callback.message.edit_text(prompts[action], reply_markup=cancel_kb(), parse_mode="HTML")
    await callback.answer()


@router.message(AdminStates.order_id_input)
async def process_order_action(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    data = await state.get_data()
    action = data.get("order_action", "search")
    try:
        order_id = int(message.text.strip())
        order = await get_order(order_id)
        if not order:
            await message.answer("❌ Order not found.")
            await state.clear()
            return
        if action == "search":
            from utils.messages import order_detail_message
            text = "🛡️ <b>ADMIN VIEW</b>\n" + order_detail_message(order)
            text += f"\n👤 <b>User ID:</b> <code>{order.user_id}</code>"
            await message.answer(text, reply_markup=admin_orders_kb(), parse_mode="HTML")
        elif action == "complete":
            await update_order_status(order_id, "completed")
            try:
                await message.bot.send_message(order.user_id, f"✅ <b>Order #{order_id} Completed!</b>\n\nYour order has been marked as completed.", parse_mode="HTML")
            except: pass
            await message.answer(f"✅ Order #{order_id} marked as completed.", reply_markup=admin_orders_kb(), parse_mode="HTML")
        elif action == "cancel":
            await update_order_status(order_id, "cancelled")
            # Refund
            await update_user_balance(order.user_id, order.price)
            try:
                await message.bot.send_message(order.user_id, f"❌ <b>Order #{order_id} Cancelled.</b>\n\n💰 {format_currency(order.price)} has been refunded to your balance.", parse_mode="HTML")
            except: pass
            await message.answer(f"❌ Order #{order_id} cancelled + refunded.", reply_markup=admin_orders_kb(), parse_mode="HTML")
        await state.clear()
    except ValueError:
        await message.answer("❌ Invalid Order ID.")


# ─────────────────────────────────────────────
# TICKET MANAGEMENT
# ─────────────────────────────────────────────

@router.message(Command("tickets"))
@router.callback_query(F.data == "adm_tickets")
async def cb_admin_tickets(event, state: FSMContext = None):
    tickets = await get_open_tickets()
    text = f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n🎫  <b>TICKET MANAGEMENT</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n📊 Open Tickets: {len(tickets)}"
    if isinstance(event, Message):
        if not is_admin(event.from_user.id): return
        await event.answer(text, reply_markup=admin_tickets_kb(), parse_mode="HTML")
    else:
        if not is_admin(event.from_user.id): return
        await event.message.edit_text(text, reply_markup=admin_tickets_kb(), parse_mode="HTML")
        await event.answer()


@router.callback_query(F.data == "adm_open_tickets")
async def cb_open_tickets(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    tickets = await get_open_tickets()
    if not tickets:
        await callback.message.edit_text("✅ No open tickets!", reply_markup=admin_tickets_kb(), parse_mode="HTML")
        await callback.answer()
        return
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()
    for t in tickets[:10]:
        builder.row(InlineKeyboardButton(text=f"🎫 #{t.id} • {t.subject[:30]}", callback_data=f"adm_viewticket_{t.id}"))
    builder.row(InlineKeyboardButton(text="◀️ Back", callback_data="adm_tickets"))
    await callback.message.edit_text(f"🎫 <b>OPEN TICKETS ({len(tickets)})</b>", reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("adm_viewticket_"))
async def cb_view_ticket(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    ticket_id = int(callback.data.split("_")[-1])
    ticket = await get_ticket(ticket_id)
    if not ticket: return
    user = await get_user(ticket.user_id)
    text = (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎫 <b>TICKET #{ticket.id}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 <b>User:</b> {user.full_name if user else ticket.user_id} (<code>{ticket.user_id}</code>)\n"
        f"📌 <b>Subject:</b> {ticket.subject}\n"
        f"📊 <b>Status:</b> {ticket.status}\n"
        f"📅 <b>Date:</b> {ticket.created_at.strftime('%d %b %Y')}\n\n"
        f"💬 <b>Message:</b>\n{ticket.message}"
    )
    await callback.message.edit_text(text, reply_markup=ticket_action_kb(ticket_id), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("adm_ticket_reply_"))
async def cb_ticket_reply_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    ticket_id = int(callback.data.split("_")[-1])
    await state.update_data(reply_ticket_id=ticket_id)
    await state.set_state(AdminStates.ticket_reply)
    await callback.message.answer(f"💬 Enter reply for Ticket #{ticket_id}:", reply_markup=cancel_kb())
    await callback.answer()


@router.message(AdminStates.ticket_reply)
async def process_ticket_reply(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    data = await state.get_data()
    ticket_id = data["reply_ticket_id"]
    await reply_ticket(ticket_id, message.from_user.id, message.text.strip())
    ticket = await get_ticket(ticket_id)
    await state.clear()
    try:
        await message.bot.send_message(
            ticket.user_id,
            f"💬 <b>Support replied to Ticket #{ticket_id}</b>\n\n📌 <b>Subject:</b> {ticket.subject}\n\n🛡️ <b>Admin Reply:</b>\n{message.text.strip()}",
            parse_mode="HTML"
        )
    except: pass
    await message.answer(f"✅ Reply sent for Ticket #{ticket_id}.", reply_markup=admin_tickets_kb(), parse_mode="HTML")


@router.callback_query(F.data.startswith("adm_ticket_close_"))
async def cb_ticket_close(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    ticket_id = int(callback.data.split("_")[-1])
    await close_ticket(ticket_id)
    await callback.answer(f"✅ Ticket #{ticket_id} closed.", show_alert=True)
    await callback.message.edit_reply_markup(reply_markup=None)


# ─────────────────────────────────────────────
# BROADCAST
# ─────────────────────────────────────────────

@router.message(Command("broadcast"))
@router.callback_query(F.data == "adm_broadcast")
async def cb_broadcast(event, state: FSMContext = None):
    if isinstance(event, Message):
        if not is_admin(event.from_user.id): return
        if state: await state.set_state(AdminStates.broadcast_message)
        await event.answer("📢 <b>BROADCAST</b>\n\nEnter the message to send to ALL users:", reply_markup=cancel_kb(), parse_mode="HTML")
    else:
        if not is_admin(event.from_user.id): return
        await state.set_state(AdminStates.broadcast_message)
        await event.message.edit_text("📢 <b>BROADCAST</b>\n\nEnter the message to send to ALL users:", reply_markup=cancel_kb(), parse_mode="HTML")
        await event.answer()


@router.message(AdminStates.broadcast_message)
async def process_broadcast_msg(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    await state.update_data(broadcast_text=message.text)
    await state.set_state(AdminStates.broadcast_confirm)
    count = await get_user_count()
    preview = (
        f"📢 <b>BROADCAST PREVIEW</b>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{message.text}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👥 Will be sent to <b>{count}</b> users.\n"
        "Confirm?"
    )
    await message.answer(preview, reply_markup=confirm_broadcast_kb(), parse_mode="HTML")


@router.callback_query(AdminStates.broadcast_confirm, F.data == "adm_broadcast_send")
async def cb_broadcast_send(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    data = await state.get_data()
    text = data["broadcast_text"]
    await state.clear()

    users = await get_all_users()
    sent, failed = 0, 0

    await callback.message.edit_text(f"📤 Sending to {len(users)} users...", reply_markup=None)

    for user in users:
        try:
            await callback.bot.send_message(user.telegram_id, f"📢 <b>Announcement from Fire Service</b>\n\n{text}", parse_mode="HTML")
            sent += 1
        except:
            failed += 1

    await callback.message.edit_text(
        f"✅ <b>Broadcast Complete!</b>\n\n✅ Sent: {sent}\n❌ Failed: {failed}",
        reply_markup=admin_main_kb(), parse_mode="HTML"
    )
    await callback.answer()


# ─────────────────────────────────────────────
# COUPONS
# ─────────────────────────────────────────────

@router.callback_query(F.data == "adm_coupons")
async def cb_admin_coupons(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    await callback.message.edit_text("🎁 <b>COUPON MANAGEMENT</b>", reply_markup=admin_coupons_kb(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "adm_create_coupon")
async def cb_create_coupon(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    await state.set_state(AdminStates.coupon_code)
    await callback.message.edit_text("➕ <b>CREATE COUPON</b>\n\nEnter coupon code (e.g. FIRE50):", reply_markup=cancel_kb(), parse_mode="HTML")
    await callback.answer()


@router.message(AdminStates.coupon_code)
async def process_coupon_code(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    await state.update_data(c_code=message.text.strip().upper())
    await state.set_state(AdminStates.coupon_type)
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="% Percent", callback_data="ctype_percent"),
        InlineKeyboardButton(text="₹ Fixed", callback_data="ctype_fixed"),
    )
    await message.answer("Select discount type:", reply_markup=builder.as_markup())


@router.callback_query(AdminStates.coupon_type, F.data.startswith("ctype_"))
async def process_coupon_type(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    ctype = callback.data.split("_")[-1]
    await state.update_data(c_type=ctype)
    await state.set_state(AdminStates.coupon_value)
    await callback.message.edit_text(f"Enter discount value ({'%' if ctype == 'percent' else '₹'}):", reply_markup=cancel_kb())
    await callback.answer()


@router.message(AdminStates.coupon_value)
async def process_coupon_value(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    try:
        await state.update_data(c_value=float(message.text.strip()))
        await state.set_state(AdminStates.coupon_max_uses)
        await message.answer("Enter maximum uses (e.g. 100):")
    except ValueError:
        await message.answer("❌ Invalid value.")


@router.message(AdminStates.coupon_max_uses)
async def process_coupon_max_uses(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    try:
        max_uses = int(message.text.strip())
        data = await state.get_data()
        coupon = await create_coupon(
            code=data["c_code"], discount_type=data["c_type"],
            discount_value=data["c_value"], max_uses=max_uses
        )
        await state.clear()
        await message.answer(
            f"✅ <b>Coupon Created!</b>\n\n"
            f"🎫 Code: <code>{coupon.code}</code>\n"
            f"💸 Discount: {coupon.discount_value}{'%' if coupon.discount_type == 'percent' else '₹'}\n"
            f"🔢 Max Uses: {coupon.max_uses}",
            reply_markup=admin_coupons_kb(), parse_mode="HTML"
        )
    except ValueError:
        await message.answer("❌ Invalid number.")


@router.callback_query(F.data == "adm_list_coupons")
async def cb_list_coupons(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    coupons = await get_all_coupons()
    if not coupons:
        await callback.answer("No coupons found.", show_alert=True)
        return
    lines = []
    for c in coupons:
        active = "✅" if c.is_active else "❌"
        disc = f"{c.discount_value}%" if c.discount_type == "percent" else format_currency(c.discount_value)
        lines.append(f"{active} <code>{c.code}</code> — {disc} | Used: {c.used_count}/{c.max_uses}")
    text = "🎁 <b>ALL COUPONS</b>\n\n" + "\n".join(lines)
    await callback.message.edit_text(text, reply_markup=admin_coupons_kb(), parse_mode="HTML")
    await callback.answer()


# ─────────────────────────────────────────────
# SETTINGS
# ─────────────────────────────────────────────

@router.message(Command("settings"))
@router.callback_query(F.data == "adm_settings")
async def cb_admin_settings(event, state: FSMContext = None):
    text = (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚙️  <b>BOT SETTINGS</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💳 <b>UPI ID:</b> {config.UPI_ID}\n"
        f"🎁 <b>Referral Bonus:</b> {format_currency(config.REFERRAL_BONUS)}\n"
        f"🎯 <b>Daily Bonus:</b> {format_currency(config.DAILY_BONUS)}\n"
        f"💰 <b>Min Deposit:</b> {format_currency(config.MIN_DEPOSIT)}\n"
        f"💰 <b>Max Deposit:</b> {format_currency(config.MAX_DEPOSIT)}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<i>Edit values in .env file and restart bot.</i>"
    )
    if isinstance(event, Message):
        if not is_admin(event.from_user.id): return
        await event.answer(text, reply_markup=admin_settings_kb(), parse_mode="HTML")
    else:
        if not is_admin(event.from_user.id): return
        await event.message.edit_text(text, reply_markup=admin_settings_kb(), parse_mode="HTML")
        await event.answer()


@router.callback_query(F.data == "adm_apis")
async def cb_admin_apis(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    from services.smm_api import smm_api
    balance = None
    try:
        balance = await smm_api.get_balance()
    except: pass
    text = (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔌  <b>API MANAGEMENT</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🌐 <b>API URL:</b> {config.SMM_API_URL[:40] if config.SMM_API_URL else '❌ Not set'}\n"
        f"🔑 <b>API Key:</b> {'✅ Configured' if config.SMM_API_KEY else '❌ Not set'}\n"
        f"💰 <b>API Balance:</b> {f'${balance:.2f}' if balance else '❌ Cannot connect'}\n\n"
        "<i>Update API credentials in .env file and restart.</i>"
    )
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="◀️ Back", callback_data="adm_main"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()
