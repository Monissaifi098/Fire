from datetime import datetime
import pytz
from config import config


def get_ist_time() -> datetime:
    tz = pytz.timezone(config.TIMEZONE)
    return datetime.now(tz)


def format_currency(amount: float) -> str:
    return f"₹{amount:,.2f}"


def format_number(n: int) -> str:
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


def get_rank_emoji(rank: str) -> str:
    rank_map = {
        "💎 Diamond": "💎",
        "🥇 Gold": "🥇",
        "🥈 Silver": "🥈",
        "🥉 Bronze": "🥉",
    }
    for k, v in rank_map.items():
        if k in rank:
            return v
    return "🥉"


def get_status_text(status: str) -> str:
    status_map = {
        "pending":     "⏳ Pending",
        "processing":  "🔄 Processing",
        "in_progress": "▶️ In Progress",
        "completed":   "✅ Completed",
        "partial":     "⚠️ Partial",
        "cancelled":   "❌ Cancelled",
        "failed":      "🚫 Failed",
    }
    return status_map.get(status, f"❓ {status.title()}")


def calculate_price(price_per_1000: float, quantity: int, is_vip: bool = False) -> float:
    price = (price_per_1000 / 1000) * quantity
    if is_vip:
        price *= 0.85  # 15% VIP discount
    return round(price, 2)


def apply_coupon_discount(price: float, discount_type: str, discount_value: float) -> float:
    if discount_type == "percent":
        discount = price * (discount_value / 100)
    else:
        discount = discount_value
    return max(0.01, round(price - discount, 2))


def truncate(text: str, max_len: int = 30) -> str:
    return text if len(text) <= max_len else text[:max_len - 1] + "…"


# ─────────────────────────────────────────────
# PREMIUM MESSAGES
# ─────────────────────────────────────────────

WELCOME_BANNER = """
╔══════════════════════════════╗
║    🔥  F I R E  S E R V I C E    🔥    ║
╚══════════════════════════════╝

<b>Welcome to the #1 Premium SMM Panel!</b>

🚀 <b>Fastest delivery</b> in India
💎 <b>Premium quality</b> guaranteed
🔒 <b>100% safe</b> & secure orders
💳 <b>Easy UPI payments</b>
⚡ <b>24/7 automated</b> service

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

def welcome_message(user_name: str, is_new: bool = False) -> str:
    greeting = "🎉 <b>New account created!</b>" if is_new else "👋 <b>Welcome back!</b>"
    return (
        WELCOME_BANNER
        + f"{greeting} <b>{user_name}</b>\n\n"
        + "Choose an option below to get started 👇"
    )


def account_message(user) -> str:
    vip_status = "👑 <b>VIP Member</b>" if user.is_vip else "🥉 Standard"
    vip_expires = ""
    if user.is_vip and user.vip_expires:
        vip_expires = f"\n👑 <b>VIP Expires:</b> {user.vip_expires.strftime('%d %b %Y')}"
    return (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "👤  <b>MY ACCOUNT</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🆔 <b>User ID:</b> <code>{user.telegram_id}</code>\n"
        f"👤 <b>Name:</b> {user.full_name or 'N/A'}\n"
        f"📛 <b>Username:</b> @{user.username or 'N/A'}\n\n"
        f"💰 <b>Balance:</b> {format_currency(user.balance)}\n"
        f"📊 <b>Total Spent:</b> {format_currency(user.total_spent)}\n"
        f"💳 <b>Total Deposited:</b> {format_currency(user.total_deposited)}\n\n"
        f"📦 <b>Total Orders:</b> {user.total_orders}\n"
        f"🏆 <b>Rank:</b> {user.rank}\n"
        f"⭐ <b>Status:</b> {vip_status}{vip_expires}\n\n"
        f"🔗 <b>Referral Code:</b> <code>{user.referral_code}</code>\n"
        f"💸 <b>Referral Earnings:</b> {format_currency(user.referral_earnings)}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )


def order_summary_message(service_name: str, link: str, quantity: int,
                           price: float, coupon_applied: bool = False,
                           original_price: float = None) -> str:
    discount_line = ""
    if coupon_applied and original_price:
        saved = original_price - price
        discount_line = f"🎫 <b>Discount:</b> -{format_currency(saved)}\n"
    return (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🛒  <b>ORDER SUMMARY</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"⚡ <b>Service:</b> {service_name}\n"
        f"🔗 <b>Link:</b> <code>{truncate(link, 40)}</code>\n"
        f"🔢 <b>Quantity:</b> {format_number(quantity)}\n"
        f"{discount_line}"
        f"💰 <b>Total Price:</b> {format_currency(price)}\n\n"
        "⚡ <i>Delivery starts within minutes after confirmation!</i>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "✅ Confirm to place this order?"
    )


def order_placed_message(order_id: int, service_name: str, quantity: int, price: float) -> str:
    return (
        "🔥 <b>ORDER PLACED SUCCESSFULLY!</b>\n\n"
        f"🆔 <b>Order ID:</b> <code>#{order_id}</code>\n"
        f"⚡ <b>Service:</b> {service_name}\n"
        f"🔢 <b>Quantity:</b> {format_number(quantity)}\n"
        f"💰 <b>Amount Deducted:</b> {format_currency(price)}\n\n"
        "🚀 <b>Your order is being processed!</b>\n"
        "📲 You'll be notified on completion.\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 <i>Track your order anytime from My Orders</i>"
    )


def order_detail_message(order) -> str:
    return (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📦  <b>ORDER #{order.id}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"⚡ <b>Service:</b> {order.service_name}\n"
        f"🔗 <b>Link:</b> <code>{truncate(order.link, 45)}</code>\n"
        f"🔢 <b>Quantity:</b> {format_number(order.quantity)}\n"
        f"💰 <b>Price:</b> {format_currency(order.price)}\n"
        f"📊 <b>Status:</b> {get_status_text(order.status)}\n"
        + (f"⏳ <b>Remains:</b> {format_number(order.remains)}\n" if order.remains else "")
        + f"📅 <b>Placed:</b> {order.created_at.strftime('%d %b %Y, %I:%M %p')}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )


def payment_instructions_message(amount: float, payment_id: int) -> str:
    return (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💳  <b>PAYMENT INSTRUCTIONS</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💰 <b>Amount to Pay:</b> {format_currency(amount)}\n"
        f"🆔 <b>Payment ID:</b> <code>#{payment_id}</code>\n\n"
        f"📲 <b>UPI ID:</b> <code>{config.UPI_ID}</code>\n"
        f"👤 <b>Payee Name:</b> {config.UPI_NAME}\n\n"
        "📌 <b>Steps:</b>\n"
        "1️⃣ Open any UPI app (GPay, PhonePe, Paytm)\n"
        "2️⃣ Send exact amount to the UPI ID above\n"
        "3️⃣ Take a screenshot of payment\n"
        "4️⃣ Click <b>I've Paid</b> and upload screenshot\n\n"
        "⚡ <i>Balance credited within 5–15 minutes after verification</i>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )


def referral_message(user) -> str:
    bot_link = f"https://t.me/{config.BOT_USERNAME}?start=ref_{user.referral_code}"
    return (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "👥  <b>REFERRAL PROGRAM</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💰 <b>Earn {format_currency(config.REFERRAL_BONUS)}</b> for every friend you refer!\n\n"
        f"🔗 <b>Your Link:</b>\n<code>{bot_link}</code>\n\n"
        f"🏷️ <b>Your Code:</b> <code>{user.referral_code}</code>\n"
        f"💸 <b>Total Earned:</b> {format_currency(user.referral_earnings)}\n\n"
        "📌 <b>How it works:</b>\n"
        "1️⃣ Share your referral link\n"
        "2️⃣ Friend joins the bot\n"
        f"3️⃣ You get {format_currency(config.REFERRAL_BONUS)} instantly!\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )


def vip_message() -> str:
    return (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "👑  <b>VIP MEMBERSHIP</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🔥 <b>VIP Benefits:</b>\n"
        "✅ 15% discount on ALL orders\n"
        "✅ 2x daily bonus\n"
        "✅ Priority support\n"
        "✅ Exclusive VIP services\n"
        "✅ Early access to new features\n"
        "✅ No rate limits\n\n"
        f"👑 <b>Monthly:</b> {format_currency(config.VIP_PRICE_MONTHLY)}/month\n"
        f"💎 <b>Yearly:</b> {format_currency(config.VIP_PRICE_YEARLY)}/year\n"
        "<i>(Save ₹{:.0f} with yearly!)</i>\n\n".format(
            config.VIP_PRICE_MONTHLY * 12 - config.VIP_PRICE_YEARLY
        ) +
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )


def stats_message(stats: dict) -> str:
    return (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📊  <b>BOT STATISTICS</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👥 <b>Total Users:</b> {stats['total_users']:,}\n"
        f"🆕 <b>New Today:</b> {stats['new_users_today']}\n\n"
        f"📦 <b>Total Orders:</b> {stats['total_orders']:,}\n"
        f"📦 <b>Orders Today:</b> {stats['orders_today']}\n\n"
        f"💰 <b>Total Revenue:</b> {format_currency(stats['total_revenue'])}\n\n"
        f"⏳ <b>Pending Payments:</b> {stats['pending_payments']}\n"
        f"🎫 <b>Open Tickets:</b> {stats['open_tickets']}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
