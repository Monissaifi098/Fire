from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from loguru import logger

from database import (
    get_user, get_categories, get_services_by_category, get_service,
    create_order, get_user_orders, get_order, get_coupon, has_used_coupon, use_coupon
)
from keyboards import categories_kb, services_kb, order_confirm_kb, orders_list_kb, order_status_kb, back_button, cancel_kb
from states import OrderStates
from utils.messages import (
    order_summary_message, order_placed_message, order_detail_message,
    format_currency, format_number, calculate_price, apply_coupon_discount
)
from services.smm_api import smm_api

router = Router()


# ─────────────────────────────────────────────
# BROWSE SERVICES
# ─────────────────────────────────────────────

@router.callback_query(F.data == "menu_order")
async def cb_order_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    categories = await get_categories()
    if not categories:
        await callback.answer("No services available right now.", show_alert=True)
        return
    text = (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🛒  <b>SELECT A CATEGORY</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "⚡ Choose a platform to boost:\n"
    )
    await callback.message.edit_text(text, reply_markup=categories_kb(categories), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("cat_"))
async def cb_select_category(callback: CallbackQuery, state: FSMContext):
    category_id = int(callback.data[4:])
    services = await get_services_by_category(category_id)
    if not services:
        await callback.answer("No services in this category.", show_alert=True)
        return
    from database import get_category
    cat = await get_category(category_id)
    text = (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{cat.emoji}  <b>{cat.name.upper()} SERVICES</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"<i>Prices shown per 1000 units in ₹</i>\n"
    )
    await state.update_data(category_id=category_id)
    await callback.message.edit_text(text, reply_markup=services_kb(services, category_id), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("svc_"))
async def cb_select_service(callback: CallbackQuery, state: FSMContext):
    service_id = int(callback.data[4:])
    service = await get_service(service_id)
    if not service:
        await callback.answer("Service not found.", show_alert=True)
        return

    user = await get_user(callback.from_user.id)

    text = (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚡  <b>SERVICE DETAILS</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📦 <b>{service.name}</b>\n\n"
        f"💰 <b>Price:</b> {format_currency(service.price_per_1000)} per 1000\n"
        f"🔢 <b>Min:</b> {format_number(service.min_quantity)}\n"
        f"🔢 <b>Max:</b> {format_number(service.max_quantity)}\n"
        f"⏱️ <b>Avg. Time:</b> {service.average_time}\n"
        f"⭐ <b>Quality:</b> {service.quality}\n"
        + (f"\n📝 {service.description}" if service.description else "")
        + f"\n\n💳 <b>Your Balance:</b> {format_currency(user.balance)}\n"
        + (f"👑 <b>VIP:</b> 15% discount applied!" if user.is_vip else "")
        + "\n\n🔗 <b>Enter the link to boost:</b>\n<i>(e.g. your Instagram profile or post URL)</i>"
    )

    await state.update_data(service_id=service_id, service_name=service.name,
                             price_per_1000=service.price_per_1000,
                             min_qty=service.min_quantity, max_qty=service.max_quantity,
                             is_vip=user.is_vip, coupon_code=None, coupon_discount=0)
    await state.set_state(OrderStates.entering_link)
    await callback.message.edit_text(text, reply_markup=cancel_kb(), parse_mode="HTML")
    await callback.answer()


# ─────────────────────────────────────────────
# ORDER FLOW
# ─────────────────────────────────────────────

@router.message(OrderStates.entering_link)
async def process_link(message: Message, state: FSMContext):
    link = message.text.strip()
    if len(link) < 5 or not ("." in link or link.startswith("@")):
        await message.answer(
            "❌ <b>Invalid link!</b>\n\nPlease enter a valid URL or username.\n"
            "<i>Example: https://instagram.com/yourprofile</i>",
            parse_mode="HTML"
        )
        return

    data = await state.get_data()
    min_qty = data.get("min_qty", 100)
    max_qty = data.get("max_qty", 100000)
    price_per_1000 = data.get("price_per_1000", 0)
    is_vip = data.get("is_vip", False)

    await state.update_data(link=link)
    await state.set_state(OrderStates.entering_quantity)

    sample_price = calculate_price(price_per_1000, 1000, is_vip)
    text = (
        f"✅ <b>Link saved!</b> <code>{link[:50]}</code>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔢  <b>ENTER QUANTITY</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📊 <b>Min:</b> {format_number(min_qty)}\n"
        f"📊 <b>Max:</b> {format_number(max_qty)}\n"
        f"💰 <b>Rate:</b> {format_currency(price_per_1000)}/1000\n"
        f"💡 <b>Example:</b> 1000 = {format_currency(sample_price)}\n\n"
        f"⌨️ Enter the quantity you want:"
    )
    await message.answer(text, reply_markup=cancel_kb(), parse_mode="HTML")


@router.message(OrderStates.entering_quantity)
async def process_quantity(message: Message, state: FSMContext):
    try:
        qty = int(message.text.strip().replace(",", "").replace(" ", ""))
    except ValueError:
        await message.answer("❌ <b>Invalid quantity!</b>\n\nPlease enter a number only.\n<i>Example: 1000</i>", parse_mode="HTML")
        return

    data = await state.get_data()
    min_qty = data.get("min_qty", 100)
    max_qty = data.get("max_qty", 100000)

    if qty < min_qty or qty > max_qty:
        await message.answer(
            f"❌ <b>Quantity out of range!</b>\n\n"
            f"📊 Min: {format_number(min_qty)}\n"
            f"📊 Max: {format_number(max_qty)}\n\n"
            f"Please enter a valid quantity.",
            parse_mode="HTML"
        )
        return

    price = calculate_price(data["price_per_1000"], qty, data.get("is_vip", False))
    await state.update_data(quantity=qty, price=price, original_price=price)

    user = await get_user(message.from_user.id)
    coupon_applied = data.get("coupon_code") is not None

    text = order_summary_message(
        data["service_name"], data["link"], qty, price,
        coupon_applied=coupon_applied, original_price=data.get("original_price")
    )
    text += f"\n\n💳 <b>Your Balance:</b> {format_currency(user.balance)}"

    if user.balance < price:
        text += f"\n\n❌ <b>Insufficient balance!</b> Need {format_currency(price - user.balance)} more."

    await state.set_state(OrderStates.confirming_order)
    await message.answer(text, reply_markup=order_confirm_kb(data), parse_mode="HTML")


@router.callback_query(OrderStates.confirming_order, F.data == "order_coupon")
async def cb_apply_coupon(callback: CallbackQuery, state: FSMContext):
    await state.set_state(OrderStates.entering_coupon)
    await callback.message.edit_text(
        "🎫 <b>APPLY COUPON</b>\n\nEnter your coupon code:",
        reply_markup=cancel_kb(), parse_mode="HTML"
    )
    await callback.answer()


@router.message(OrderStates.entering_coupon)
async def process_coupon(message: Message, state: FSMContext):
    code = message.text.strip().upper()
    coupon = await get_coupon(code)

    if not coupon:
        await message.answer("❌ <b>Invalid coupon code!</b>\n\nPlease check and try again.", parse_mode="HTML")
        await state.set_state(OrderStates.confirming_order)
        return

    if coupon.used_count >= coupon.max_uses:
        await message.answer("❌ <b>Coupon expired!</b>\n\nThis coupon has reached its usage limit.", parse_mode="HTML")
        await state.set_state(OrderStates.confirming_order)
        return

    already_used = await has_used_coupon(coupon.id, message.from_user.id)
    if already_used:
        await message.answer("❌ <b>Already used!</b>\n\nYou've already used this coupon.", parse_mode="HTML")
        await state.set_state(OrderStates.confirming_order)
        return

    data = await state.get_data()
    original_price = data.get("original_price", data["price"])
    new_price = apply_coupon_discount(original_price, coupon.discount_type, coupon.discount_value)

    discount_display = f"{coupon.discount_value}%" if coupon.discount_type == "percent" else format_currency(coupon.discount_value)
    saved = original_price - new_price

    await state.update_data(price=new_price, coupon_code=code, coupon_id=coupon.id,
                             coupon_discount=saved, original_price=original_price)
    await state.set_state(OrderStates.confirming_order)

    text = (
        f"✅ <b>Coupon Applied!</b>\n\n"
        f"🎫 Code: <code>{code}</code>\n"
        f"💸 Discount: {discount_display}\n"
        f"💰 Saved: {format_currency(saved)}\n"
        f"💳 New Price: {format_currency(new_price)}\n"
    )
    user = await get_user(message.from_user.id)
    text += f"\n💳 <b>Your Balance:</b> {format_currency(user.balance)}"

    await message.answer(text, reply_markup=order_confirm_kb({}), parse_mode="HTML")


@router.callback_query(OrderStates.confirming_order, F.data == "order_confirm")
async def cb_confirm_order(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user = await get_user(callback.from_user.id)

    price = data["price"]

    if user.balance < price:
        await callback.answer("❌ Insufficient balance! Please add funds.", show_alert=True)
        return

    # Place order via API
    service = await get_service(data["service_id"])
    api_order_id = None

    if service and service.api_service_id:
        try:
            api_order_id = await smm_api.place_order(
                service.api_service_id, data["link"], data["quantity"]
            )
        except Exception as e:
            logger.error(f"API order failed: {e}")

    order = await create_order(
        user_id=callback.from_user.id,
        service_id=data["service_id"],
        service_name=data["service_name"],
        link=data["link"],
        quantity=data["quantity"],
        price=price,
        api_order_id=api_order_id,
    )

    # Mark coupon as used
    if data.get("coupon_id"):
        await use_coupon(data["coupon_id"], callback.from_user.id)

    # Update rank
    from database import update_user_rank
    await update_user_rank(callback.from_user.id)

    await state.clear()
    text = order_placed_message(order.id, data["service_name"], data["quantity"], price)
    await callback.message.edit_text(text, reply_markup=order_status_kb(order.id), parse_mode="HTML")
    await callback.answer("🔥 Order placed!", show_alert=True)


@router.callback_query(OrderStates.confirming_order, F.data == "order_cancel")
async def cb_cancel_order(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "❌ <b>Order cancelled.</b>",
        reply_markup=__import__("keyboards").main_menu_kb(), parse_mode="HTML"
    )
    await callback.answer("Order cancelled.")


# ─────────────────────────────────────────────
# MY ORDERS
# ─────────────────────────────────────────────

@router.callback_query(F.data == "menu_orders")
async def cb_my_orders(callback: CallbackQuery):
    orders = await get_user_orders(callback.from_user.id, limit=10)
    if not orders:
        text = (
            "📦 <b>MY ORDERS</b>\n\n"
            "You haven't placed any orders yet.\n\n"
            "Click 🛒 <b>Order Services</b> to get started!"
        )
        from keyboards import back_to_main_kb
        await callback.message.edit_text(text, reply_markup=back_to_main_kb(), parse_mode="HTML")
    else:
        text = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📦  <b>MY ORDERS</b>  ({len(orders)} recent)\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Tap an order to view details:"
        )
        await callback.message.edit_text(text, reply_markup=orders_list_kb(orders), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("order_detail_"))
async def cb_order_detail(callback: CallbackQuery):
    order_id = int(callback.data.split("_")[-1])
    order = await get_order(order_id)

    if not order or order.user_id != callback.from_user.id:
        await callback.answer("Order not found.", show_alert=True)
        return

    text = order_detail_message(order)
    await callback.message.edit_text(text, reply_markup=order_status_kb(order_id), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("order_status_"))
async def cb_refresh_order_status(callback: CallbackQuery):
    order_id = int(callback.data.split("_")[-1])
    order = await get_order(order_id)

    if not order:
        await callback.answer("Order not found.", show_alert=True)
        return

    # Try to update from API
    if order.api_order_id:
        try:
            api_status = await smm_api.get_order_status(order.api_order_id)
            if api_status and "status" in api_status:
                status_map = {
                    "Pending": "pending", "In progress": "in_progress",
                    "Processing": "processing", "Completed": "completed",
                    "Partial": "partial", "Cancelled": "cancelled"
                }
                new_status = status_map.get(api_status["status"], order.status)
                remains = api_status.get("remains")
                from database import update_order_status
                await update_order_status(order_id, new_status, remains)
                order = await get_order(order_id)
        except Exception as e:
            logger.warning(f"Status check failed for order {order_id}: {e}")

    text = order_detail_message(order)
    await callback.message.edit_text(text, reply_markup=order_status_kb(order_id), parse_mode="HTML")
    await callback.answer("✅ Status refreshed!")
