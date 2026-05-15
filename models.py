from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, BigInteger, ForeignKey
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(100), nullable=True)
    full_name = Column(String(200), nullable=True)
    balance = Column(Float, default=0.0)
    total_spent = Column(Float, default=0.0)
    total_deposited = Column(Float, default=0.0)
    referral_code = Column(String(20), unique=True, nullable=True)
    referred_by = Column(BigInteger, nullable=True)
    referral_earnings = Column(Float, default=0.0)
    rank = Column(String(20), default="Bronze")
    is_vip = Column(Boolean, default=False)
    vip_expires = Column(DateTime, nullable=True)
    is_banned = Column(Boolean, default=False)
    ban_reason = Column(Text, nullable=True)
    language = Column(String(10), default="en")
    daily_bonus_claimed = Column(DateTime, nullable=True)
    total_orders = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    last_active = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    emoji = Column(String(10), default="📦")
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())


class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    api_service_id = Column(String(50), nullable=True)  # SMM panel API service ID
    price_per_1000 = Column(Float, nullable=False)       # Price per 1000 units in INR
    min_quantity = Column(Integer, default=100)
    max_quantity = Column(Integer, default=100000)
    is_active = Column(Boolean, default=True)
    average_time = Column(String(50), default="0-24 hours")
    quality = Column(String(20), default="High Quality")
    created_at = Column(DateTime, server_default=func.now())


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    service_name = Column(String(200), nullable=False)
    link = Column(Text, nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    status = Column(String(30), default="pending")
    # Status: pending, processing, in_progress, completed, partial, cancelled, failed
    api_order_id = Column(String(100), nullable=True)  # Order ID from SMM API
    start_count = Column(Integer, nullable=True)
    remains = Column(Integer, nullable=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    method = Column(String(50), default="UPI")
    transaction_id = Column(String(200), nullable=True)
    screenshot_file_id = Column(String(500), nullable=True)
    status = Column(String(20), default="pending")
    # Status: pending, approved, rejected
    admin_note = Column(Text, nullable=True)
    approved_by = Column(BigInteger, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Coupon(Base):
    __tablename__ = "coupons"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False)
    discount_type = Column(String(20), default="percent")  # percent / fixed
    discount_value = Column(Float, nullable=False)
    min_order = Column(Float, default=0.0)
    max_uses = Column(Integer, default=100)
    used_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class CouponUsage(Base):
    __tablename__ = "coupon_usage"

    id = Column(Integer, primary_key=True, autoincrement=True)
    coupon_id = Column(Integer, ForeignKey("coupons.id"), nullable=False)
    user_id = Column(BigInteger, nullable=False)
    used_at = Column(DateTime, server_default=func.now())


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    subject = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String(20), default="open")  # open, in_progress, closed
    admin_reply = Column(Text, nullable=True)
    replied_by = Column(BigInteger, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Referral(Base):
    __tablename__ = "referrals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    referrer_id = Column(BigInteger, nullable=False)
    referred_id = Column(BigInteger, nullable=False)
    bonus_paid = Column(Float, default=0.0)
    created_at = Column(DateTime, server_default=func.now())


class BroadcastLog(Base):
    __tablename__ = "broadcast_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    admin_id = Column(BigInteger, nullable=False)
    message = Column(Text, nullable=False)
    sent_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
