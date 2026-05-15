from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from loguru import logger

from config import config
from database import get_user, create_ticket, get_ticket, get_user_tickets
from keyboards import support_kb, ticket_list_kb, back_to_main_kb, cancel_kb
from states import TicketStates
from utils.messages import format_currency

router = Router()


@router.callback_query(F.data == "menu_support")
async def cb_support(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    tickets = await get_user_tickets(callback.from_user.id)
    open_count = sum(1 for t in tickets if t.status != "closed")
    text = (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🆘  <b>SUPPORT CENTER</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📋 <b>Your Tickets:</b> {len(tickets)} total, {open_count} open\n\n"
        "💬 Having an issue? Create a support ticket!\n"
        "Our team responds within 24 hours.\n\n"
        f"📞 Direct Support: {config.SUPPORT_USERNAME}"
    )
    await callback.message.edit_text(text, reply_markup=support_kb(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "ticket_create")
async def cb_ticket_create(callback: CallbackQuery, state: FSMContext):
    await state.set_state(TicketStates.entering_subject)
    text = (
        "🎫 <b>CREATE SUPPORT TICKET</b>\n\n"
        "Step 1/2: Enter a brief subject for your issue:\n"
        "<i>Example: Order #123 not delivered</i>"
    )
    await callback.message.edit_text(text, reply_markup=cancel_kb(), parse_mode="HTML")
    await callback.answer()


@router.message(TicketStates.entering_subject)
async def process_ticket_subject(message: Message, state: FSMContext):
    subject = message.text.strip()
    if len(subject) < 5:
        await message.answer("❌ Subject too short. Please be more descriptive.", parse_mode="HTML")
        return
    if len(subject) > 100:
        await message.answer("❌ Subject too long. Max 100 characters.", parse_mode="HTML")
        return
    await state.update_data(subject=subject)
    await state.set_state(TicketStates.entering_message)
    text = (
        f"✅ <b>Subject:</b> {subject}\n\n"
        "Step 2/2: Describe your issue in detail:"
    )
    await message.answer(text, reply_markup=cancel_kb(), parse_mode="HTML")


@router.message(TicketStates.entering_message)
async def process_ticket_message(message: Message, state: FSMContext):
    msg = message.text.strip()
    if len(msg) < 10:
        await message.answer("❌ Please provide more details (min 10 chars).", parse_mode="HTML")
        return

    data = await state.get_data()
    ticket = await create_ticket(
        user_id=message.from_user.id,
        subject=data["subject"],
        message=msg
    )
    await state.clear()

    # Notify admins
    text_admin = (
        "🎫 <b>NEW SUPPORT TICKET</b>\n\n"
        f"🆔 <b>Ticket ID:</b> #{ticket.id}\n"
        f"👤 <b>User:</b> {message.from_user.full_name} (<code>{message.from_user.id}</code>)\n"
        f"📌 <b>Subject:</b> {data['subject']}\n\n"
        f"💬 <b>Message:</b>\n{msg}"
    )
    from keyboards import ticket_action_kb
    for admin_id in config.ADMIN_IDS:
        try:
            await message.bot.send_message(admin_id, text_admin, reply_markup=ticket_action_kb(ticket.id), parse_mode="HTML")
        except Exception as e:
            logger.warning(f"Failed to notify admin {admin_id}: {e}")

    text = (
        "✅ <b>Ticket Created Successfully!</b>\n\n"
        f"🆔 <b>Ticket ID:</b> #{ticket.id}\n"
        f"📌 <b>Subject:</b> {data['subject']}\n"
        f"📊 <b>Status:</b> 🔴 Open\n\n"
        "⏳ Our team will respond within 24 hours.\n"
        "You'll be notified when we reply!"
    )
    await message.answer(text, reply_markup=back_to_main_kb(), parse_mode="HTML")


@router.callback_query(F.data == "ticket_list")
async def cb_ticket_list(callback: CallbackQuery):
    tickets = await get_user_tickets(callback.from_user.id)
    if not tickets:
        text = (
            "📋 <b>MY TICKETS</b>\n\n"
            "You haven't created any tickets yet.\n\n"
            "Need help? Create a new ticket!"
        )
        await callback.message.edit_text(text, reply_markup=support_kb(), parse_mode="HTML")
    else:
        text = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📋  <b>MY TICKETS</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Tap a ticket to view details:"
        )
        await callback.message.edit_text(text, reply_markup=ticket_list_kb(tickets), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("ticket_view_"))
async def cb_ticket_view(callback: CallbackQuery):
    ticket_id = int(callback.data.split("_")[-1])
    ticket = await get_ticket(ticket_id)

    if not ticket or ticket.user_id != callback.from_user.id:
        await callback.answer("Ticket not found.", show_alert=True)
        return

    status_map = {"open": "🔴 Open", "in_progress": "🟡 In Progress", "closed": "🟢 Closed"}
    status = status_map.get(ticket.status, ticket.status)

    text = (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎫  <b>TICKET #{ticket.id}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📌 <b>Subject:</b> {ticket.subject}\n"
        f"📊 <b>Status:</b> {status}\n"
        f"📅 <b>Created:</b> {ticket.created_at.strftime('%d %b %Y, %I:%M %p')}\n\n"
        f"💬 <b>Your Message:</b>\n{ticket.message}\n"
    )
    if ticket.admin_reply:
        text += f"\n🛡️ <b>Admin Reply:</b>\n{ticket.admin_reply}\n"
    text += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    await callback.message.edit_text(text, reply_markup=back_to_main_kb(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "menu_coupons")
async def cb_coupons(callback: CallbackQuery):
    text = (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🎫  <b>COUPON CODES</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Have a coupon code? Apply it during checkout!\n\n"
        "🛒 Go to <b>Order Services</b>\n"
        "➡️ Select service and quantity\n"
        "➡️ Tap <b>Apply Coupon</b> before confirming\n\n"
        "🔥 Follow our Telegram channel for exclusive coupons!\n"
        f"📢 {config.SUPPORT_USERNAME}"
    )
    await callback.message.edit_text(text, reply_markup=back_to_main_kb(), parse_mode="HTML")
    await callback.answer()
