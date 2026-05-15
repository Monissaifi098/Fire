from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from typing import List
from database.models import Category, Service


# ─────────────────────────────────────────────
# MAIN MENU
# ─────────────────────────────────────────────

def main_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🛒 Order Services", callback_data="menu_order"),
        InlineKeyboardButton(text="👤 My Account", callback_data="menu_account"),
    )
    builder.row(
        InlineKeyboardButton(text="💳 Add Funds", callback_data="menu_add_funds"),
        InlineKeyboardButton(text="📦 My Orders", callback_data="menu_orders"),
    )
    builder.row(
        InlineKeyboardButton(text="🎁 Daily Bonus", callback_data="menu_daily_bonus"),
        InlineKeyboardButton(text="👥 Referral", callback_data="menu_referral"),
    )
    builder.row(
        InlineKeyboardButton(text="🎫 Coupons", callback_data="menu_coupons"),
        InlineKeyboardButton(text="🆘 Support", callback_data="menu_support"),
    )
    builder.row(
        InlineKeyboardButton(text="👑 VIP Plans", callback_data="menu_vip"),
        InlineKeyboardButton(text="ℹ️ Help", callback_data="menu_help"),
    )
    return builder.as_markup()


def back_to_main_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🏠 Main Menu", callback_data="menu_main"))
    return builder.as_markup()


def back_button(callback: str = "menu_main") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="◀️ Back", callback_data=callback),
        InlineKeyboardButton(text="🏠 Home", callback_data="menu_main"),
    )
    return builder.as_markup()


# ─────────────────────────────────────────────
# CATEGORIES
# ─────────────────────────────────────────────

def categories_kb(categories: List[Category]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.row(InlineKeyboardButton(
            text=f"{cat.emoji} {cat.name}",
            callback_data=f"cat_{cat.id}"
        ))
    builder.row(InlineKeyboardButton(text="🏠 Main Menu", callback_data="menu_main"))
    return builder.as_markup()


def services_kb(services: List[Service], category_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for svc in services:
        price = svc.price_per_1000
        builder.row(InlineKeyboardButton(
            text=f"⚡ {svc.name}  •  ₹{price}/1K",
            callback_data=f"svc_{svc.id}"
        ))
    builder.row(
        InlineKeyboardButton(text="◀️ Back", callback_data="menu_order"),
        InlineKeyboardButton(text="🏠 Home", callback_data="menu_main"),
    )
    return builder.as_markup()


# ─────────────────────────────────────────────
# ORDER
# ─────────────────────────────────────────────

def order_confirm_kb(order_data: dict) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Confirm Order", callback_data="order_confirm"),
        InlineKeyboardButton(text="❌ Cancel", callback_data="order_cancel"),
    )
    builder.row(InlineKeyboardButton(text="🎫 Apply Coupon", callback_data="order_coupon"))
    return builder.as_markup()


def order_status_kb(order_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔄 Refresh Status", callback_data=f"order_status_{order_id}"))
    builder.row(InlineKeyboardButton(text="🏠 Main Menu", callback_data="menu_main"))
    return builder.as_markup()


def orders_list_kb(orders) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for order in orders[:8]:
        status_emoji = {
            "pending": "⏳", "processing": "🔄", "in_progress": "▶️",
            "completed": "✅", "cancelled": "❌", "partial": "⚠️", "failed": "🚫"
        }.get(order.status, "❓")
        builder.row(InlineKeyboardButton(
            text=f"{status_emoji} #{order.id} • {order.service_name[:25]}",
            callback_data=f"order_detail_{order.id}"
        ))
    builder.row(InlineKeyboardButton(text="🏠 Main Menu", callback_data="menu_main"))
    return builder.as_markup()


# ─────────────────────────────────────────────
# PAYMENT
# ─────────────────────────────────────────────

def add_funds_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for amount in [49, 99, 199, 499, 999, 1999]:
        builder.button(text=f"₹{amount}", callback_data=f"fund_preset_{amount}")
    builder.adjust(3)
    builder.row(InlineKeyboardButton(text="💬 Custom Amount", callback_data="fund_custom"))
    builder.row(InlineKeyboardButton(text="🏠 Main Menu", callback_data="menu_main"))
    return builder.as_markup()


def payment_confirm_kb(payment_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📸 I've Paid — Submit Screenshot", callback_data=f"pay_submit_{payment_id}"))
    builder.row(InlineKeyboardButton(text="❌ Cancel", callback_data="menu_main"))
    return builder.as_markup()


# ─────────────────────────────────────────────
# SUPPORT / TICKETS
# ─────────────────────────────────────────────

def support_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🎫 Create New Ticket", callback_data="ticket_create"))
    builder.row(InlineKeyboardButton(text="📋 My Tickets", callback_data="ticket_list"))
    builder.row(InlineKeyboardButton(text="🏠 Main Menu", callback_data="menu_main"))
    return builder.as_markup()


def ticket_list_kb(tickets) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for ticket in tickets[:8]:
        status_emoji = {"open": "🔴", "in_progress": "🟡", "closed": "🟢"}.get(ticket.status, "❓")
        builder.row(InlineKeyboardButton(
            text=f"{status_emoji} #{ticket.id} • {ticket.subject[:30]}",
            callback_data=f"ticket_view_{ticket.id}"
        ))
    builder.row(InlineKeyboardButton(text="◀️ Back", callback_data="menu_support"))
    return builder.as_markup()


# ─────────────────────────────────────────────
# VIP
# ─────────────────────────────────────────────

def vip_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="👑 Monthly VIP — ₹299", callback_data="vip_monthly"))
    builder.row(InlineKeyboardButton(text="💎 Yearly VIP — ₹2499", callback_data="vip_yearly"))
    builder.row(InlineKeyboardButton(text="🏠 Main Menu", callback_data="menu_main"))
    return builder.as_markup()


# ─────────────────────────────────────────────
# ADMIN KEYBOARDS
# ─────────────────────────────────────────────

def admin_main_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📊 Statistics", callback_data="adm_stats"),
        InlineKeyboardButton(text="👥 Users", callback_data="adm_users"),
    )
    builder.row(
        InlineKeyboardButton(text="📦 Services", callback_data="adm_services"),
        InlineKeyboardButton(text="💳 Payments", callback_data="adm_payments"),
    )
    builder.row(
        InlineKeyboardButton(text="📝 Orders", callback_data="adm_orders"),
        InlineKeyboardButton(text="🎫 Tickets", callback_data="adm_tickets"),
    )
    builder.row(
        InlineKeyboardButton(text="📢 Broadcast", callback_data="adm_broadcast"),
        InlineKeyboardButton(text="🎁 Coupons", callback_data="adm_coupons"),
    )
    builder.row(
        InlineKeyboardButton(text="⚙️ Settings", callback_data="adm_settings"),
        InlineKeyboardButton(text="🔌 APIs", callback_data="adm_apis"),
    )
    builder.row(InlineKeyboardButton(text="🏠 Main Menu", callback_data="menu_main"))
    return builder.as_markup()


def admin_users_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔍 Find User", callback_data="adm_find_user"))
    builder.row(InlineKeyboardButton(text="💰 Add Balance", callback_data="adm_add_balance"))
    builder.row(InlineKeyboardButton(text="🚫 Ban User", callback_data="adm_ban_user"))
    builder.row(InlineKeyboardButton(text="✅ Unban User", callback_data="adm_unban_user"))
    builder.row(InlineKeyboardButton(text="👑 Grant VIP", callback_data="adm_grant_vip"))
    builder.row(InlineKeyboardButton(text="◀️ Back", callback_data="adm_main"))
    return builder.as_markup()


def admin_services_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="➕ Add Category", callback_data="adm_add_category"))
    builder.row(InlineKeyboardButton(text="➕ Add Service", callback_data="adm_add_service"))
    builder.row(InlineKeyboardButton(text="📋 List Services", callback_data="adm_list_services"))
    builder.row(InlineKeyboardButton(text="✏️ Edit Service", callback_data="adm_edit_service"))
    builder.row(InlineKeyboardButton(text="🗑️ Delete Service", callback_data="adm_delete_service"))
    builder.row(InlineKeyboardButton(text="◀️ Back", callback_data="adm_main"))
    return builder.as_markup()


def admin_payments_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⏳ Pending Payments", callback_data="adm_pending_payments"))
    builder.row(InlineKeyboardButton(text="📋 All Payments", callback_data="adm_all_payments"))
    builder.row(InlineKeyboardButton(text="◀️ Back", callback_data="adm_main"))
    return builder.as_markup()


def payment_action_kb(payment_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Approve", callback_data=f"adm_pay_approve_{payment_id}"),
        InlineKeyboardButton(text="❌ Reject", callback_data=f"adm_pay_reject_{payment_id}"),
    )
    builder.row(InlineKeyboardButton(text="◀️ Back", callback_data="adm_payments"))
    return builder.as_markup()


def admin_orders_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔍 Search Order", callback_data="adm_search_order"))
    builder.row(InlineKeyboardButton(text="📋 Recent Orders", callback_data="adm_recent_orders"))
    builder.row(InlineKeyboardButton(text="✅ Force Complete", callback_data="adm_force_complete"))
    builder.row(InlineKeyboardButton(text="❌ Force Cancel", callback_data="adm_force_cancel"))
    builder.row(InlineKeyboardButton(text="◀️ Back", callback_data="adm_main"))
    return builder.as_markup()


def admin_tickets_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔴 Open Tickets", callback_data="adm_open_tickets"))
    builder.row(InlineKeyboardButton(text="◀️ Back", callback_data="adm_main"))
    return builder.as_markup()


def ticket_action_kb(ticket_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💬 Reply", callback_data=f"adm_ticket_reply_{ticket_id}"),
        InlineKeyboardButton(text="🔒 Close", callback_data=f"adm_ticket_close_{ticket_id}"),
    )
    builder.row(InlineKeyboardButton(text="◀️ Back", callback_data="adm_tickets"))
    return builder.as_markup()


def admin_coupons_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="➕ Create Coupon", callback_data="adm_create_coupon"))
    builder.row(InlineKeyboardButton(text="📋 List Coupons", callback_data="adm_list_coupons"))
    builder.row(InlineKeyboardButton(text="◀️ Back", callback_data="adm_main"))
    return builder.as_markup()


def admin_settings_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="💳 Update UPI ID", callback_data="adm_set_upi"))
    builder.row(InlineKeyboardButton(text="🎁 Referral Bonus", callback_data="adm_set_referral"))
    builder.row(InlineKeyboardButton(text="🎯 Daily Bonus", callback_data="adm_set_daily"))
    builder.row(InlineKeyboardButton(text="◀️ Back", callback_data="adm_main"))
    return builder.as_markup()


def admin_categories_select_kb(categories) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.row(InlineKeyboardButton(
            text=f"{cat.emoji} {cat.name}",
            callback_data=f"adm_selcat_{cat.id}"
        ))
    builder.row(InlineKeyboardButton(text="◀️ Cancel", callback_data="adm_services"))
    return builder.as_markup()


def confirm_broadcast_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Send Now", callback_data="adm_broadcast_send"),
        InlineKeyboardButton(text="❌ Cancel", callback_data="adm_main"),
    )
    return builder.as_markup()


def cancel_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="❌ Cancel", callback_data="menu_main"))
    return builder.as_markup()
