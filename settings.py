import os
from dotenv import load_dotenv
from typing import List

load_dotenv()

class Config:
    # Bot
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    BOT_USERNAME: str = os.getenv("BOT_USERNAME", "FireServiceBot")
    BOT_NAME: str = os.getenv("BOT_NAME", "🔥 Fire Service")

    # Admins
    ADMIN_IDS: List[int] = [
        int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()
    ]

    # SMM API
    SMM_API_URL: str = os.getenv("SMM_API_URL", "")
    SMM_API_KEY: str = os.getenv("SMM_API_KEY", "")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///fire_service.db")

    # UPI
    UPI_ID: str = os.getenv("UPI_ID", "yourname@upi")
    UPI_NAME: str = os.getenv("UPI_NAME", "Fire Service")
    UPI_QR_IMAGE_URL: str = os.getenv("UPI_QR_IMAGE_URL", "")

    # Support
    SUPPORT_USERNAME: str = os.getenv("SUPPORT_USERNAME", "@FireServiceSupport")

    # Limits
    MIN_DEPOSIT: float = float(os.getenv("MIN_DEPOSIT", "10"))
    MAX_DEPOSIT: float = float(os.getenv("MAX_DEPOSIT", "100000"))
    REFERRAL_BONUS: float = float(os.getenv("REFERRAL_BONUS", "10"))
    DAILY_BONUS: float = float(os.getenv("DAILY_BONUS", "2"))
    VIP_PRICE_MONTHLY: float = float(os.getenv("VIP_PRICE_MONTHLY", "299"))
    VIP_PRICE_YEARLY: float = float(os.getenv("VIP_PRICE_YEARLY", "2499"))

    # Rate Limiting
    RATE_LIMIT_MESSAGES: int = int(os.getenv("RATE_LIMIT_MESSAGES", "10"))
    RATE_LIMIT_PERIOD: int = int(os.getenv("RATE_LIMIT_PERIOD", "60"))

    # Timezone
    TIMEZONE: str = os.getenv("TIMEZONE", "Asia/Kolkata")

config = Config()
