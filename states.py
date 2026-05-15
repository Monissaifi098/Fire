from aiogram.fsm.state import State, StatesGroup


class OrderStates(StatesGroup):
    selecting_category = State()
    selecting_service = State()
    entering_link = State()
    entering_quantity = State()
    entering_coupon = State()
    confirming_order = State()


class PaymentStates(StatesGroup):
    entering_amount = State()
    entering_transaction_id = State()
    uploading_screenshot = State()
    confirming_payment = State()


class TicketStates(StatesGroup):
    entering_subject = State()
    entering_message = State()


class AdminStates(StatesGroup):
    # Service management
    add_service_category = State()
    add_service_name = State()
    add_service_price = State()
    add_service_min = State()
    add_service_max = State()
    add_service_api_id = State()
    add_service_time = State()

    # Category management
    add_category_name = State()
    add_category_emoji = State()
    add_category_desc = State()

    # User management
    find_user = State()
    add_balance_user_id = State()
    add_balance_amount = State()
    ban_user_id = State()
    ban_reason = State()

    # Broadcast
    broadcast_message = State()
    broadcast_confirm = State()

    # Coupon
    coupon_code = State()
    coupon_type = State()
    coupon_value = State()
    coupon_min_order = State()
    coupon_max_uses = State()

    # Ticket reply
    ticket_reply = State()

    # Settings
    settings_upi_id = State()
    settings_referral_bonus = State()
    settings_daily_bonus = State()

    # Order management
    order_id_input = State()

    # Edit service
    edit_service_field = State()
    edit_service_value = State()
