# ربات صرافی تلگرام (sarraf-bot)

ربات تلگرامی برای خدمات تبادل ارز دیجیتال — فارسی، بدون پایگاه داده، مکالمه‌محور.

---

## نصب و راه‌اندازی

### ۱. دریافت کد و نصب پیش‌نیازها

```bash
git clone <repo-url>
cd sarraf-bot

python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### ۲. تنظیم متغیرهای محیطی

فایل `.env.example` را به `.env` کپی کنید و مقادیر را پر کنید:

```bash
cp .env.example .env
nano .env
```

مقادیر مورد نیاز:

| متغیر | توضیح |
|---|---|
| `BOT_TOKEN` | توکن ربات از @BotFather |
| `ADMIN_CHAT_ID` | شناسه عددی ادمین (مرحله بعد) |

### ۳. دریافت ADMIN_CHAT_ID

1. ادمین (مرجان) باید یک بار دستور `/start` را برای ربات ارسال کند.
2. لاگ ربات را بررسی کنید — شناسه عددی در خروجی نمایش داده می‌شود.
3. آن عدد را در فایل `.env` در `ADMIN_CHAT_ID` قرار دهید.

> روش سریع‌تر: ادمین می‌تواند به @userinfobot پیام بدهد و ID خود را ببیند.

### ۴. اجرای مستقیم (تست)

```bash
python -m bot.main
```

---

## استقرار با systemd روی VPS

### انتقال فایل‌ها به سرور

```bash
scp -r sarraf-bot/ user@your-vps:/opt/sarraf-bot
```

### نصب سرویس

```bash
# کپی فایل سرویس
sudo cp /opt/sarraf-bot/bot.service /etc/systemd/system/bot.service

# ساخت venv روی سرور
cd /opt/sarraf-bot
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# فعال‌سازی و شروع سرویس
sudo systemctl daemon-reload
sudo systemctl enable bot
sudo systemctl start bot
```

### بررسی وضعیت

```bash
sudo systemctl status bot
sudo journalctl -u bot -f        # لاگ زنده
```

---

## ساختار پروژه

```
sarraf-bot/
├── bot/
│   ├── __init__.py
│   ├── main.py         # نقطه ورود
│   ├── handlers.py     # ConversationHandler و تمام مراحل
│   ├── config.py       # BOT_TOKEN، ADMIN_CHAT_ID
│   └── utils.py        # تبدیل ارقام فارسی، فرمت مبلغ، ساعت تهران
├── requirements.txt
├── bot.service         # فایل systemd
├── .env.example
└── README.md
```

---

## جریان مکالمه

```
/start
  └─► آدرس کیف پول
        └─► انتخاب ارز (USDT / TRX)
              └─► انتخاب شبکه
                    └─► مبلغ به تومان
                          └─► ارسال رسید (عکس یا متن)
                                └─► تأیید خودکار پس از ۲ دقیقه
                                      ├─► پیام تأیید برای کاربر
                                      └─► اطلاع‌رسانی به ادمین
```

در هر مرحله `/cancel` عملیات را لغو می‌کند.
