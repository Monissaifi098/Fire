from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import selectinload
from contextlib import asynccontextmanager
from typing import Optional, List
from datetime import datetime, timedelta
import random
import string
import pytz

from config import config
from database.models import Base, User, Category, Service, Order, Payment, Coupon, CouponUsage, Ticket, Referral, BroadcastLog
from loguru import logger

engine = create_async_engine(config.DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await seed_default_data()
    logger.info("✅ Database initialized successfully")


@asynccontextmanager
async def get_session():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def generate_referral_code(length=8):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


# ─────────────────────────────────────────────
# USER OPERATIONS
# ─────────────────────────────────────────────

async def get_or_create_user(telegram_id: int, username: str = None, full_name: str = None, referred_by: int = None) -> User:
    async with get_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if not user:
            ref_code = generate_referral_code()
            user = User(
                telegram_id=telegram_id,
                username=username,
                full_name=full_name,
                referral_code=ref_code,
                referred_by=referred_by,
            )
            session.add(user)
            await session.flush()
            # Credit referral bonus
            if referred_by:
                await session.execute(
                    update(User).where(User.telegram_id == referred_by)
                    .values(balance=User.balance + config.REFERRAL_BONUS,
                            referral_earnings=User.referral_earnings + config.REFERRAL_BONUS)
                )
                ref_entry = Referral(referrer_id=referred_by, referred_id=telegram_id, bonus_paid=config.REFERRAL_BONUS)
                session.add(ref_entry)
        else:
            user.username = username or user.username
            user.full_name = full_name or user.full_name
            user.last_active = datetime.utcnow()
        return user


async def get_user(telegram_id: int) -> Optional[User]:
    async with get_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalar_one_or_none()


async def update_user_balance(telegram_id: int, amount: float):
    async with get_session() as session:
        await session.execute(
            update(User).where(User.telegram_id == telegram_id)
            .values(balance=User.balance + amount)
        )


async def set_user_balance(telegram_id: int, amount: float):
    async with get_session() as session:
        await session.execute(
            update(User).where(User.telegram_id == telegram_id)
            .values(balance=amount)
        )


async def ban_user(telegram_id: int, reason: str):
    async with get_session() as session:
        await session.execute(
            update(User).where(User.telegram_id == telegram_id)
            .values(is_banned=True, ban_reason=reason)
        )


async def unban_user(telegram_id: int):
    async with get_session() as session:
        await session.execute(
            update(User).where(User.telegram_id == telegram_id)
            .values(is_banned=False, ban_reason=None)
        )


async def get_all_users() -> List[User]:
    async with get_session() as session:
        result = await session.execute(select(User).order_by(User.created_at.desc()))
        return result.scalars().all()


async def get_user_count() -> int:
    async with get_session() as session:
        result = await session.execute(select(func.count(User.id)))
        return result.scalar()


async def claim_daily_bonus(telegram_id: int) -> tuple[bool, float]:
    async with get_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if not user:
            return False, 0
        now = datetime.utcnow()
        if user.daily_bonus_claimed:
            last = user.daily_bonus_claimed
            if (now - last).total_seconds() < 86400:
                return False, 0
        bonus = config.DAILY_BONUS
        if user.is_vip:
            bonus *= 2
        user.daily_bonus_claimed = now
        user.balance += bonus
        return True, bonus


async def update_user_rank(telegram_id: int):
    async with get_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if not user:
            return
        spent = user.total_spent
        if spent >= 10000:
            rank = "💎 Diamond"
        elif spent >= 5000:
            rank = "🥇 Gold"
        elif spent >= 1000:
            rank = "🥈 Silver"
        else:
            rank = "🥉 Bronze"
        user.rank = rank


async def get_user_referrals(telegram_id: int) -> List[Referral]:
    async with get_session() as session:
        result = await session.execute(
            select(Referral).where(Referral.referrer_id == telegram_id)
        )
        return result.scalars().all()


# ─────────────────────────────────────────────
# CATEGORY OPERATIONS
# ─────────────────────────────────────────────

async def get_categories() -> List[Category]:
    async with get_session() as session:
        result = await session.execute(
            select(Category).where(Category.is_active == True).order_by(Category.sort_order)
        )
        return result.scalars().all()


async def get_all_categories() -> List[Category]:
    async with get_session() as session:
        result = await session.execute(select(Category).order_by(Category.sort_order))
        return result.scalars().all()


async def get_category(category_id: int) -> Optional[Category]:
    async with get_session() as session:
        result = await session.execute(select(Category).where(Category.id == category_id))
        return result.scalar_one_or_none()


async def create_category(name: str, emoji: str, description: str = "") -> Category:
    async with get_session() as session:
        cat = Category(name=name, emoji=emoji, description=description)
        session.add(cat)
        await session.flush()
        return cat


async def update_category(category_id: int, **kwargs):
    async with get_session() as session:
        await session.execute(update(Category).where(Category.id == category_id).values(**kwargs))


async def delete_category(category_id: int):
    async with get_session() as session:
        await session.execute(delete(Category).where(Category.id == category_id))


# ─────────────────────────────────────────────
# SERVICE OPERATIONS
# ─────────────────────────────────────────────

async def get_services_by_category(category_id: int) -> List[Service]:
    async with get_session() as session:
        result = await session.execute(
            select(Service).where(
                and_(Service.category_id == category_id, Service.is_active == True)
            )
        )
        return result.scalars().all()


async def get_all_services() -> List[Service]:
    async with get_session() as session:
        result = await session.execute(select(Service))
        return result.scalars().all()


async def get_service(service_id: int) -> Optional[Service]:
    async with get_session() as session:
        result = await session.execute(select(Service).where(Service.id == service_id))
        return result.scalar_one_or_none()


async def create_service(category_id: int, name: str, price_per_1000: float,
                          min_qty: int, max_qty: int, api_service_id: str = "",
                          description: str = "", avg_time: str = "0-24 hours") -> Service:
    async with get_session() as session:
        svc = Service(
            category_id=category_id, name=name, price_per_1000=price_per_1000,
            min_quantity=min_qty, max_quantity=max_qty, api_service_id=api_service_id,
            description=description, average_time=avg_time
        )
        session.add(svc)
        await session.flush()
        return svc


async def update_service(service_id: int, **kwargs):
    async with get_session() as session:
        await session.execute(update(Service).where(Service.id == service_id).values(**kwargs))


async def delete_service(service_id: int):
    async with get_session() as session:
        await session.execute(delete(Service).where(Service.id == service_id))


# ─────────────────────────────────────────────
# ORDER OPERATIONS
# ─────────────────────────────────────────────

async def create_order(user_id: int, service_id: int, service_name: str,
                        link: str, quantity: int, price: float, api_order_id: str = None) -> Order:
    async with get_session() as session:
        order = Order(
            user_id=user_id, service_id=service_id, service_name=service_name,
            link=link, quantity=quantity, price=price, api_order_id=api_order_id,
            status="processing"
        )
        session.add(order)
        await session.execute(
            update(User).where(User.telegram_id == user_id)
            .values(balance=User.balance - price,
                    total_spent=User.total_spent + price,
                    total_orders=User.total_orders + 1)
        )
        await session.flush()
        return order


async def get_user_orders(user_id: int, limit: int = 10) -> List[Order]:
    async with get_session() as session:
        result = await session.execute(
            select(Order).where(Order.user_id == user_id)
            .order_by(Order.created_at.desc()).limit(limit)
        )
        return result.scalars().all()


async def get_order(order_id: int) -> Optional[Order]:
    async with get_session() as session:
        result = await session.execute(select(Order).where(Order.id == order_id))
        return result.scalar_one_or_none()


async def update_order_status(order_id: int, status: str, remains: int = None):
    async with get_session() as session:
        vals = {"status": status}
        if remains is not None:
            vals["remains"] = remains
        await session.execute(update(Order).where(Order.id == order_id).values(**vals))


async def get_all_orders(limit: int = 50) -> List[Order]:
    async with get_session() as session:
        result = await session.execute(
            select(Order).order_by(Order.created_at.desc()).limit(limit)
        )
        return result.scalars().all()


async def get_total_revenue() -> float:
    async with get_session() as session:
        result = await session.execute(select(func.sum(Order.price)).where(Order.status == "completed"))
        return result.scalar() or 0.0


async def get_order_count() -> int:
    async with get_session() as session:
        result = await session.execute(select(func.count(Order.id)))
        return result.scalar()


# ─────────────────────────────────────────────
# PAYMENT OPERATIONS
# ─────────────────────────────────────────────

async def create_payment(user_id: int, amount: float, transaction_id: str = None,
                          screenshot_file_id: str = None) -> Payment:
    async with get_session() as session:
        payment = Payment(
            user_id=user_id, amount=amount,
            transaction_id=transaction_id, screenshot_file_id=screenshot_file_id
        )
        session.add(payment)
        await session.flush()
        return payment


async def get_payment(payment_id: int) -> Optional[Payment]:
    async with get_session() as session:
        result = await session.execute(select(Payment).where(Payment.id == payment_id))
        return result.scalar_one_or_none()


async def approve_payment(payment_id: int, admin_id: int):
    async with get_session() as session:
        result = await session.execute(select(Payment).where(Payment.id == payment_id))
        payment = result.scalar_one_or_none()
        if not payment or payment.status != "pending":
            return False
        payment.status = "approved"
        payment.approved_by = admin_id
        payment.updated_at = datetime.utcnow()
        await session.execute(
            update(User).where(User.telegram_id == payment.user_id)
            .values(balance=User.balance + payment.amount,
                    total_deposited=User.total_deposited + payment.amount)
        )
        return True


async def reject_payment(payment_id: int, admin_id: int, note: str = ""):
    async with get_session() as session:
        await session.execute(
            update(Payment).where(Payment.id == payment_id)
            .values(status="rejected", approved_by=admin_id, admin_note=note)
        )


async def get_pending_payments() -> List[Payment]:
    async with get_session() as session:
        result = await session.execute(
            select(Payment).where(Payment.status == "pending").order_by(Payment.created_at.desc())
        )
        return result.scalars().all()


async def get_user_payments(user_id: int) -> List[Payment]:
    async with get_session() as session:
        result = await session.execute(
            select(Payment).where(Payment.user_id == user_id).order_by(Payment.created_at.desc()).limit(10)
        )
        return result.scalars().all()


# ─────────────────────────────────────────────
# COUPON OPERATIONS
# ─────────────────────────────────────────────

async def get_coupon(code: str) -> Optional[Coupon]:
    async with get_session() as session:
        result = await session.execute(
            select(Coupon).where(and_(Coupon.code == code.upper(), Coupon.is_active == True))
        )
        return result.scalar_one_or_none()


async def use_coupon(coupon_id: int, user_id: int):
    async with get_session() as session:
        await session.execute(
            update(Coupon).where(Coupon.id == coupon_id)
            .values(used_count=Coupon.used_count + 1)
        )
        usage = CouponUsage(coupon_id=coupon_id, user_id=user_id)
        session.add(usage)


async def has_used_coupon(coupon_id: int, user_id: int) -> bool:
    async with get_session() as session:
        result = await session.execute(
            select(CouponUsage).where(
                and_(CouponUsage.coupon_id == coupon_id, CouponUsage.user_id == user_id)
            )
        )
        return result.scalar_one_or_none() is not None


async def create_coupon(code: str, discount_type: str, discount_value: float,
                         min_order: float = 0, max_uses: int = 100) -> Coupon:
    async with get_session() as session:
        coupon = Coupon(
            code=code.upper(), discount_type=discount_type,
            discount_value=discount_value, min_order=min_order, max_uses=max_uses
        )
        session.add(coupon)
        await session.flush()
        return coupon


async def get_all_coupons() -> List[Coupon]:
    async with get_session() as session:
        result = await session.execute(select(Coupon).order_by(Coupon.created_at.desc()))
        return result.scalars().all()


# ─────────────────────────────────────────────
# TICKET OPERATIONS
# ─────────────────────────────────────────────

async def create_ticket(user_id: int, subject: str, message: str) -> Ticket:
    async with get_session() as session:
        ticket = Ticket(user_id=user_id, subject=subject, message=message)
        session.add(ticket)
        await session.flush()
        return ticket


async def get_ticket(ticket_id: int) -> Optional[Ticket]:
    async with get_session() as session:
        result = await session.execute(select(Ticket).where(Ticket.id == ticket_id))
        return result.scalar_one_or_none()


async def reply_ticket(ticket_id: int, admin_id: int, reply: str):
    async with get_session() as session:
        await session.execute(
            update(Ticket).where(Ticket.id == ticket_id)
            .values(admin_reply=reply, replied_by=admin_id, status="in_progress",
                    updated_at=datetime.utcnow())
        )


async def close_ticket(ticket_id: int):
    async with get_session() as session:
        await session.execute(
            update(Ticket).where(Ticket.id == ticket_id).values(status="closed")
        )


async def get_open_tickets() -> List[Ticket]:
    async with get_session() as session:
        result = await session.execute(
            select(Ticket).where(Ticket.status.in_(["open", "in_progress"]))
            .order_by(Ticket.created_at.desc())
        )
        return result.scalars().all()


async def get_user_tickets(user_id: int) -> List[Ticket]:
    async with get_session() as session:
        result = await session.execute(
            select(Ticket).where(Ticket.user_id == user_id).order_by(Ticket.created_at.desc())
        )
        return result.scalars().all()


# ─────────────────────────────────────────────
# STATS
# ─────────────────────────────────────────────

async def get_stats() -> dict:
    async with get_session() as session:
        total_users = (await session.execute(select(func.count(User.id)))).scalar() or 0
        total_orders = (await session.execute(select(func.count(Order.id)))).scalar() or 0
        total_revenue = (await session.execute(select(func.sum(Order.price)).where(Order.status.in_(["completed", "processing", "in_progress"])))).scalar() or 0
        pending_payments = (await session.execute(select(func.count(Payment.id)).where(Payment.status == "pending"))).scalar() or 0
        open_tickets = (await session.execute(select(func.count(Ticket.id)).where(Ticket.status.in_(["open", "in_progress"])))).scalar() or 0
        today = datetime.utcnow().date()
        new_users_today = (await session.execute(
            select(func.count(User.id)).where(func.date(User.created_at) == today)
        )).scalar() or 0
        orders_today = (await session.execute(
            select(func.count(Order.id)).where(func.date(Order.created_at) == today)
        )).scalar() or 0
        return {
            "total_users": total_users,
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "pending_payments": pending_payments,
            "open_tickets": open_tickets,
            "new_users_today": new_users_today,
            "orders_today": orders_today,
        }


# ─────────────────────────────────────────────
# SEED DEFAULT DATA
# ─────────────────────────────────────────────

async def seed_default_data():
    async with get_session() as session:
        result = await session.execute(select(func.count(Category.id)))
        if result.scalar() > 0:
            return
        logger.info("🌱 Seeding default categories and services...")
        categories_data = [
            ("Instagram", "📸", "Instagram followers, likes, views", [
                ("Instagram Followers [Indian]", 49.0, 100, 50000, "60-120 mins"),
                ("Instagram Followers [Global HQ]", 29.0, 100, 100000, "0-6 hours"),
                ("Instagram Likes [Real]", 15.0, 50, 50000, "0-30 mins"),
                ("Instagram Reels Views", 5.0, 500, 1000000, "0-5 mins"),
                ("Instagram Story Views", 4.0, 100, 500000, "0-10 mins"),
            ]),
            ("YouTube", "▶️", "YouTube views, subscribers, likes", [
                ("YouTube Views [HQ]", 8.0, 1000, 5000000, "0-1 hour"),
                ("YouTube Subscribers [Real]", 89.0, 100, 10000, "1-3 days"),
                ("YouTube Likes", 20.0, 100, 100000, "0-30 mins"),
                ("YouTube Watch Hours", 199.0, 100, 5000, "2-5 days"),
            ]),
            ("TikTok", "🎵", "TikTok followers, likes, views", [
                ("TikTok Followers [HQ]", 35.0, 100, 50000, "0-6 hours"),
                ("TikTok Likes [Real]", 12.0, 100, 500000, "0-30 mins"),
                ("TikTok Views", 3.0, 1000, 10000000, "0-5 mins"),
            ]),
            ("Telegram", "✈️", "Telegram members, views, reactions", [
                ("Telegram Members [Real Indian]", 99.0, 100, 10000, "0-6 hours"),
                ("Telegram Post Views", 2.0, 1000, 10000000, "0-5 mins"),
                ("Telegram Reactions 👍", 10.0, 100, 100000, "0-15 mins"),
                ("Telegram Channel Subscribers", 79.0, 100, 50000, "0-12 hours"),
            ]),
            ("Facebook", "📘", "Facebook followers, likes, page fans", [
                ("Facebook Page Likes [HQ]", 45.0, 100, 50000, "0-12 hours"),
                ("Facebook Followers", 30.0, 100, 50000, "0-6 hours"),
                ("Facebook Post Likes", 18.0, 100, 100000, "0-30 mins"),
            ]),
            ("Twitter/X", "🐦", "Twitter followers, likes, retweets", [
                ("Twitter Followers [Real]", 55.0, 100, 25000, "0-12 hours"),
                ("Twitter Likes", 15.0, 100, 100000, "0-30 mins"),
                ("Twitter Retweets", 25.0, 100, 50000, "0-2 hours"),
            ]),
            ("Spotify", "🎧", "Spotify plays, followers, saves", [
                ("Spotify Plays [Worldwide]", 12.0, 1000, 10000000, "0-6 hours"),
                ("Spotify Followers", 79.0, 100, 10000, "0-24 hours"),
                ("Spotify Monthly Listeners", 99.0, 1000, 100000, "1-3 days"),
            ]),
            ("Website Traffic", "🌐", "Real website visitors", [
                ("Website Traffic [India]", 20.0, 1000, 1000000, "0-24 hours"),
                ("Website Traffic [Worldwide]", 10.0, 1000, 5000000, "0-6 hours"),
            ]),
        ]
        for sort_idx, (cat_name, cat_emoji, cat_desc, services) in enumerate(categories_data):
            cat = Category(name=cat_name, emoji=cat_emoji, description=cat_desc, sort_order=sort_idx)
            session.add(cat)
            await session.flush()
            for svc_name, price, min_q, max_q, avg_time in services:
                svc = Service(
                    category_id=cat.id, name=svc_name,
                    price_per_1000=price, min_quantity=min_q,
                    max_quantity=max_q, average_time=avg_time
                )
                session.add(svc)
        logger.info("✅ Default data seeded")
