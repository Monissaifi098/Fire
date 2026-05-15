from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from loguru import logger

from config import config
from database import get_user, create_payment, get_payment, get_user_payments
from keyboards import add_funds_kb, back_to_main_kb, cancel_kb
from states import PaymentStates
from utils.messages import payment_instructions_message, format_currency

router = Router()


@router.callback_query(F.data == "menu_add_funds")
async def cb_add_funds(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user = await get_user(callback.from_user.id)
    text = (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💳  <b>ADD FUNDS</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💰 <b>Current Balance:</b> {format_currency(user.balance)}\n\n"
        f"📌 <b>Min Deposit:</b> {format_currency(config.MIN_DEPOSIT)}\n"
        f"📌 <b>Max Deposit:</b> {format_currency(config.MAX_DEPOSIT)}\n\n"
        "Select a preset amount or enter a custom amount:"
    )
    await callback.message.edit_text(text, reply_markup=add_funds_kb(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("fund_preset_"))
async def cb_fund_preset(callback: CallbackQuery, state: FSMContext):
    amount = float(callback.data.split("_")[-1])
    await _show_payment_qr(callback, state, amount)


@router.callback_query(F.data == "fund_custom")
async def cb_fund_custom(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PaymentStates.entering_amount)
    text = (
        "💬 <b>CUSTOM AMOUNT</b>\n\n"
        f"Enter the amount you want to add (₹{config.MIN_DEPOSIT:.0f} – ₹{config.MAX_DEPOSIT:.0f}):"
    )
    await callback.message.edit_text(text, reply_markup=cancel_kb(), parse_mode="HTML")
    await callback.answer()


@router.message(PaymentStates.entering_amount)
async def process_custom_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.strip().replace(",", "").replace("₹", ""))
    except ValueError:
        await message.answer("❌ <b>Invalid amount!</b>\n\nPlease enter a number.\n<i>Example: 499</i>", parse_mode="HTML")
        return

    if amount < config.MIN_DEPOSIT:
        await message.answer(f"❌ Minimum deposit is {format_currency(config.MIN_DEPOSIT)}", parse_mode="HTML")
        return
    if amount > config.MAX_DEPOSIT:
        await message.answer(f"❌ Maximum deposit is {format_currency(config.MAX_DEPOSIT)}", parse_mode="HTML")
        return

    await state.clear()
    # Create a mock callback-like flow
    payment = await create_payment(user_id=message.from_user.id, amount=amount)
    text = payment_instructions_message(amount, payment.id)

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📸 I've Paid — Submit Screenshot", callback_data=f"pay_submit_{payment.id}"))
    builder.row(InlineKeyboardButton(text="❌ Cancel", callback_data="menu_main"))

    if config.UPI_QR_IMAGE_URL:
        await message.answer_photo(
            photo=config.UPI_QR_IMAGE_URL,
            caption=text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    else:
        await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")


async def _show_payment_qr(callback: CallbackQuery, state: FSMContext, amount: float):
    await state.clear()
    payment = await create_payment(user_id=callback.from_user.id, amount=amount)
    text = payment_instructions_message(amount, payment.id)

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📸 I've Paid — Submit Screenshot", callback_data=f"pay_submit_{payment.id}"))
    builder.row(InlineKeyboardButton(text="❌ Cancel", callback_data="menu_main"))

    if config.UPI_QR_IMAGE_URL:
        await callback.message.answer_photo(
            photo=config.UPI_QR_IMAGE_URL,
            caption=text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        await callback.message.delete()
    else:
        await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("pay_submit_"))
async def cb_pay_submit(callback: CallbackQuery, state: FSMContext):
    payment_id = int(callback.data.split("_")[-1])
    payment = await get_payment(payment_id)

    if not payment or payment.user_id != callback.from_user.id:
        await callback.answer("Payment not found.", show_alert=True)
        return

    if payment.status != "pending":
        await callback.answer("This payment is already processed.", show_alert=True)
        return

    await state.update_data(payment_id=payment_id)
    await state.set_state(PaymentStates.uploading_screenshot)

    text = (
        "📸 <b>SUBMIT PAYMENT PROOF</b>\n\n"
        f"💰 <b>Amount:</b> {format_currency(payment.amount)}\n"
        f"🆔 <b>Payment ID:</b> #{payment_id}\n\n"
        "📤 <b>Please send:</b>\n"
        "• Screenshot of payment\n"
        "• OR enter your Transaction ID (UTR number)\n\n"
        "<i>Send screenshot as photo or type UTR number:</i>"
    )
    await callback.message.answer(text, reply_markup=cancel_kb(), parse_mode="HTML")
    await callback.answer()


@router.message(PaymentStates.uploading_screenshot, F.photo)
async def process_screenshot(message: Message, state: FSMContext):
    data = await state.get_data()
    payment_id = data.get("payment_id")

    photo = message.photo[-1]
    file_id = photo.file_id

    from database.db import get_session
    from sqlalchemy import update
    from database.models import Payment
    async with get_session() as session:
        await session.execute(
            update(Payment).where(Payment.id == payment_id)
            .values(screenshot_file_id=file_id)
        )

    await state.clear()

    payment = await get_payment(payment_id)

    # Notify admins
    text_admin = (
        "💳 <b>NEW PAYMENT REQUEST</b>\n\n"
        f"👤 <b>User ID:</b> <code>{message.from_user.id}</code>\n"
        f"👤 <b>Name:</b> {message.from_user.full_name}\n"
        f"💰 <b>Amount:</b> {format_currency(payment.amount)}\n"
        f"🆔 <b>Payment ID:</b> #{payment_id}\n"
        f"📅 <b>Time:</b> {payment.created_at.strftime('%d %b %Y, %I:%M %p')}"
    )
    from keyboards import payment_action_kb
    for admin_id in config.ADMIN_IDS:
        try:
            await message.bot.send_photo(
                chat_id=admin_id,
                photo=file_id,
                caption=text_admin,
                reply_markup=payment_action_kb(payment_id),
                parse_mode="HTML"
            )
        except Exception as e:
            logger.warning(f"Failed to notify admin {admin_id}: {e}")

    text = (
        "✅ <b>Payment proof submitted!</b>\n\n"
        f"💰 <b>Amount:</b> {format_currency(payment.amount)}\n"
        f"🆔 <b>Payment ID:</b> #{payment_id}\n\n"
        "⏳ <b>Status:</b> Under review\n\n"
        "📲 Your balance will be credited within <b>5–15 minutes</b> after admin verification."
    )
    await message.answer(text, reply_markup=back_to_main_kb(), parse_mode="HTML")


@router.message(PaymentStates.uploading_screenshot)
async def process_transaction_id(message: Message, state: FSMContext):
    data = await state.get_data()
    payment_id = data.get("payment_id")
    txn_id = message.text.strip()

    from database.db import get_session
    from sqlalchemy import update
    from database.models import Payment
    async with get_session() as session:
        await session.execute(
            update(Payment).where(Payment.id == payment_id)
            .values(transaction_id=txn_id)
        )

    await state.clear()
    payment = await get_payment(payment_id)

    # Notify admins
    text_admin = (
        "💳 <b>NEW PAYMENT REQUEST</b>\n\n"
        f"👤 <b>User ID:</b> <code>{message.from_user.id}</code>\n"
        f"👤 <b>Name:</b> {message.from_user.full_name}\n"
        f"💰 <b>Amount:</b> {format_currency(payment.amount)}\n"
        f"🆔 <b>Payment ID:</b> #{payment_id}\n"
        f"🔖 <b>Transaction ID:</b> <code>{txn_id}</code>\n"
        f"📅 <b>Time:</b> {payment.created_at.strftime('%d %b %Y, %I:%M %p')}"
    )
    from keyboards import payment_action_kb
    for admin_id in config.ADMIN_IDS:
        try:
            await message.bot.send_message(
                chat_id=admin_id,
                text=text_admin,
                reply_markup=payment_action_kb(payment_id),
                parse_mode="HTML"
            )
        except Exception as e:
            logger.warning(f"Failed to notify admin {admin_id}: {e}")

    text = (
        "✅ <b>Payment details submitted!</b>\n\n"
        f"💰 <b>Amount:</b> {format_currency(payment.amount)}\n"
        f"🔖 <b>Transaction ID:</b> <code>{txn_id}</code>\n\n"
        "⏳ Balance will be credited within <b>5–15 minutes</b>."
    )
    await message.answer(text, reply_markup=back_to_main_kb(), parse_mode="HTML")
