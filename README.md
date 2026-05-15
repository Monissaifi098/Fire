# 🔥 Fire Service — Premium Telegram SMM Panel Bot

A production-ready Telegram bot for selling Social Media Marketing (SMM) services — Instagram, YouTube, TikTok, Telegram, and more — with a full admin panel built entirely inside Telegram.

---

## 📁 Folder Structure

```
fire_service_bot/
├── main.py                    # Entry point
├── requirements.txt
├── .env.example               # Copy to .env and fill in
│
├── config/
│   ├── __init__.py
│   └── settings.py            # Loads .env config
│
├── database/
│   ├── __init__.py
│   ├── models.py              # SQLAlchemy ORM models
│   └── db.py                  # All CRUD operations
│
├── handlers/
│   ├── __init__.py
│   ├── start.py               # /start, account, VIP, referral, daily bonus
│   ├── orders.py              # Order flow (browse → link → qty → confirm)
│   ├── payments.py            # UPI payment flow
│   ├── support.py             # Tickets + coupons
│   └── admin.py               # Full admin panel
│
├── keyboards/
│   ├── __init__.py
│   └── keyboards.py           # All inline keyboards
│
├── middlewares/
│   ├── __init__.py
│   └── middlewares.py         # Rate limiting + ban check
│
├── states/
│   ├── __init__.py
│   └── states.py              # FSM states for all flows
│
├── utils/
│   ├── __init__.py
│   └── messages.py            # All message templates + formatters
│
└── services/
    ├── __init__.py
    └── smm_api.py             # SMM Panel API v2 integration
```

---

## ⚡ Quick Setup

### 1. Clone / Download the project

```bash
cd fire_service_bot
```

### 2. Create virtual environment

```bash
python3 -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

```bash
cp .env.example .env
nano .env
```

Fill in your values:

| Key | Description |
|-----|-------------|
| `BOT_TOKEN` | From [@BotFather](https://t.me/BotFather) |
| `ADMIN_IDS` | Your Telegram User ID(s) (comma separated) |
| `SMM_API_URL` | Your SMM provider API URL |
| `SMM_API_KEY` | Your SMM provider API key |
| `UPI_ID` | Your UPI ID for receiving payments |
| `UPI_QR_IMAGE_URL` | Public URL of your QR code image (optional) |

### 5. Run the bot

```bash
python main.py
```

---

## 🔑 Getting Your Admin ID

1. Message [@userinfobot](https://t.me/userinfobot) on Telegram
2. It will show your numeric User ID
3. Put that in `ADMIN_IDS` in `.env`

---

## 🔌 SMM API Integration

This bot works with **any SMM panel** that uses the standard SMM API v2 format, including:

- [JustAnotherPanel](https://justanotherpanel.com)
- [Peakerr](https://peakerr.com)
- [SMMHeaven](https://smmheaven.com)
- And hundreds of other providers

**How to connect your API:**

1. Sign up on your chosen SMM provider
2. Get your API URL and API Key from their dashboard
3. Add to your `.env` file
4. When adding services in the admin panel, use the service IDs from your provider's API

**To get service IDs from your provider:**

```
POST https://your-provider.com/api/v2
key=YOUR_KEY&action=services
```

---

## 👤 User Features

| Feature | How to Access |
|---------|---------------|
| Welcome / Start | `/start` |
| Browse & Order Services | 🛒 Order Services button |
| Account Dashboard | 👤 My Account button |
| Add Funds (UPI) | 💳 Add Funds button |
| Order History | 📦 My Orders button |
| Daily Bonus | 🎁 Daily Bonus button |
| Referral Program | 👥 Referral button |
| Apply Coupons | During checkout |
| Support Tickets | 🆘 Support button |
| VIP Membership | 👑 VIP Plans button |

---

## 🛡️ Admin Panel

Access with `/admin` command (only works for IDs in `ADMIN_IDS`).

### Admin Commands

| Command | Function |
|---------|----------|
| `/admin` | Open admin panel |
| `/stats` | View bot statistics |
| `/users` | User management |
| `/services` | Service management |
| `/payments` | Payment approvals |
| `/tickets` | Support tickets |
| `/broadcast` | Send message to all users |
| `/settings` | View bot settings |

### Admin Features

- 📊 **Statistics** — Users, orders, revenue, pending items
- 👥 **User Management** — Find user, add balance, ban/unban, grant VIP
- 📦 **Service Management** — Add/edit/delete categories and services
- 💳 **Payment Approvals** — Approve/reject with one tap
- 📝 **Order Management** — View, force complete, force cancel + refund
- 🎫 **Ticket Management** — Reply to and close support tickets
- 📢 **Broadcast** — Send announcement to all users
- 🎁 **Coupons** — Create percent or fixed discount coupons
- 🔌 **API Status** — Check SMM API connection and balance

---

## 💳 Payment Flow

```
User taps Add Funds
  → Selects preset or custom amount
  → Bot shows UPI ID + QR code
  → User pays via GPay/PhonePe/Paytm
  → User submits screenshot or UTR number
  → Admin receives notification with Approve/Reject buttons
  → Admin taps Approve → balance credited instantly
  → User receives confirmation notification
```

---

## 🛒 Order Flow

```
User taps Order Services
  → Selects category (Instagram, YouTube, etc.)
  → Selects service
  → Enters profile/post link
  → Enters quantity
  → (Optional) Applies coupon code
  → Confirms order
  → Balance deducted
  → Order placed via SMM API
  → User can track status anytime
```

---

## 🏆 Rank System

| Rank | Requirement |
|------|-------------|
| 🥉 Bronze | < ₹1,000 spent |
| 🥈 Silver | ₹1,000+ spent |
| 🥇 Gold | ₹5,000+ spent |
| 💎 Diamond | ₹10,000+ spent |

---

## 👑 VIP Benefits

- 15% discount on all orders
- 2x daily bonus
- Priority support

---

## 🔒 Security Features

- Admin ID whitelist (only hardcoded IDs can access admin)
- Rate limiting (10 messages per minute per user)
- Ban system (banned users can't use the bot)
- SQL injection protection (SQLAlchemy ORM)
- Input validation on all user inputs
- Environment variable separation (no secrets in code)

---

## 🚀 Production Deployment (Linux VPS)

### Using systemd

Create `/etc/systemd/system/fireservice.service`:

```ini
[Unit]
Description=Fire Service Telegram Bot
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/fire_service_bot
ExecStart=/opt/fire_service_bot/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable fireservice
sudo systemctl start fireservice
sudo systemctl status fireservice
```

### View logs

```bash
sudo journalctl -u fireservice -f
```

---

## 📦 Database

Uses **SQLite** by default (stored as `fire_service.db`).

Tables:
- `users` — All registered users
- `categories` — Service categories
- `services` — Individual SMM services
- `orders` — All placed orders
- `payments` — All payment requests
- `coupons` — Discount coupons
- `coupon_usage` — Tracks who used which coupon
- `tickets` — Support tickets
- `referrals` — Referral relationships
- `broadcast_logs` — Broadcast history

Default categories and services are **auto-seeded** on first run.

---

## ❓ Troubleshooting

**Bot doesn't respond:**
- Check `BOT_TOKEN` is correct
- Make sure bot is not blocked by you
- Check `python main.py` output for errors

**Admin panel not working:**
- Make sure your Telegram ID is in `ADMIN_IDS` in `.env`
- IDs must be numeric, not username

**Orders not going to API:**
- Check `SMM_API_URL` and `SMM_API_KEY` in `.env`
- Set the correct API Service ID when creating services

**Payments not getting approved:**
- Admin must tap the Approve button in their Telegram
- Make sure admin IDs are correct

---

## 📞 Support

Built with ❤️ using Python + Aiogram 3.x

Tech stack:
- **Python 3.10+**
- **Aiogram 3.x** — Telegram bot framework
- **SQLAlchemy + aiosqlite** — Async database
- **aiohttp** — SMM API calls
- **loguru** — Logging
