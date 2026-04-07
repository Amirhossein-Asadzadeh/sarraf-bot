"""
ConversationHandler states and all step handlers for the sarraf (صرافی) bot.
"""

import asyncio
import logging
from typing import Any

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
)
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from .config import ADMIN_CHAT_ID
from .utils import format_amount, parse_amount, randomize_amount, tehran_now_str

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Conversation states
# ---------------------------------------------------------------------------
GET_WALLET, GET_CURRENCY, GET_NETWORK, GET_AMOUNT, GET_RECEIPT = range(5)

# ---------------------------------------------------------------------------
# Persian names for currencies
# ---------------------------------------------------------------------------
CURRENCY_FA = {
    "USDT": "تتر",
    "TRX":  "ترون",
}

# ---------------------------------------------------------------------------
# Persistent reply keyboard (shown outside conversation)
# ---------------------------------------------------------------------------
MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [[KeyboardButton("ثبت درخواست جدید 🆕")]],
    resize_keyboard=True,
    is_persistent=True,
)

NEW_REQUEST_FILTER = filters.Regex(r"^ثبت درخواست جدید")

# ---------------------------------------------------------------------------
# Inline keyboards
# ---------------------------------------------------------------------------
CURRENCY_KEYBOARD = InlineKeyboardMarkup(
    [[
        InlineKeyboardButton("USDT — تتر",  callback_data="USDT"),
        InlineKeyboardButton("TRX — ترون",  callback_data="TRX"),
    ]]
)

NETWORK_KEYBOARDS: dict[str, InlineKeyboardMarkup] = {
    "USDT": InlineKeyboardMarkup([[
        InlineKeyboardButton("TRC20", callback_data="TRC20"),
        InlineKeyboardButton("ERC20", callback_data="ERC20"),
        InlineKeyboardButton("BEP20", callback_data="BEP20"),
    ]]),
    "TRX": InlineKeyboardMarkup([[
        InlineKeyboardButton("TRON", callback_data="TRON"),
    ]]),
}

# ---------------------------------------------------------------------------
# Helper: send delayed confirmation
# ---------------------------------------------------------------------------
async def _send_confirmation(bot: Any, chat_id: int, data: dict) -> None:
    """Wait 120 s, then send confirmation to user and forward to admin."""
    await asyncio.sleep(120)

    now_str        = tehran_now_str()
    user_id        = data["user_id"]
    username       = data["username"]
    wallet         = data["wallet_address"]
    currency       = data["currency"]
    network        = data["network"]
    amount         = data["amount"]
    final_amount   = data["final_amount"]
    payment_amount = data.get("payment_amount", final_amount)
    currency_fa    = CURRENCY_FA.get(currency, currency)

    # ── Confirmation to user ──────────────────────────────────────────────
    await bot.send_message(
        chat_id=chat_id,
        text=(
            "تراکنش شما تأیید شد\n\n"
            f"شناسه کاربری: <code>{user_id}</code>\n\n"
            f"مبلغ کل واریزی: <b>{format_amount(payment_amount)} تومان</b>\n"
            f"کارمزد صرافی: {format_amount(final_amount - amount)} تومان\n"
            f"مبلغ واریز شده: {format_amount(amount)} تومان\n\n"
            f"زمان تراکنش: {now_str}\n\n"
            "📌 لطفاً این پیام را برای طرف مقابل فوروارد کنید."
        ),
        parse_mode="HTML",
        reply_markup=MAIN_KEYBOARD,
    )

    # ── Forward to admin ──────────────────────────────────────────────────
    if not ADMIN_CHAT_ID:
        logger.warning(
            "ADMIN_CHAT_ID not configured — skipping admin notification for user %s",
            user_id,
        )
        return

    try:
        if data["receipt_type"] == "photo":
            await bot.send_photo(
                chat_id=ADMIN_CHAT_ID,
                photo=data["receipt_file_id"],
                caption=f"رسید کاربر @{username} (ID: {user_id})",
            )
        else:
            await bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=(
                    f"📎 رسید کاربر @{username} (ID: {user_id}):\n\n"
                    f"{data['receipt_text']}"
                ),
            )

        await bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=(
                "📥 <b>سفارش جدید</b>\n\n"
                f"👤 کاربر: @{username} (ID: <code>{user_id}</code>)\n"
                f"💰 مبلغ: {format_amount(amount)} + کارمزد = <b>{format_amount(final_amount)} تومان</b>\n"
                f"📬 کیف پول:\n<code>{wallet}</code>\n"
                f"🪙 ارز: {currency} ({currency_fa}) / {network}\n"
                f"🕐 زمان: {now_str}"
            ),
            parse_mode="HTML",
        )
    except Exception:
        logger.exception("Failed to notify admin for user %s", user_id)


# ---------------------------------------------------------------------------
# Step 1 — /start  یا  دکمه «ثبت درخواست جدید»
# ---------------------------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(
        "سلام! به صرافی میراکل خوش آمدید. 🪙\n\n"
        "لطفاً آدرس کیف پول گیرنده را وارد کنید:",
        reply_markup=ReplyKeyboardRemove(),
    )
    return GET_WALLET


# ---------------------------------------------------------------------------
# Step 2 — receive wallet address
# ---------------------------------------------------------------------------
async def get_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    wallet = update.message.text.strip()
    context.user_data["wallet_address"] = wallet

    await update.message.reply_text(
        "ارز مورد نظر را انتخاب کنید:",
        reply_markup=CURRENCY_KEYBOARD,
    )
    return GET_CURRENCY


# ---------------------------------------------------------------------------
# Step 3 — receive currency (callback)
# ---------------------------------------------------------------------------
async def get_currency(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    currency = query.data
    context.user_data["currency"] = currency

    await query.edit_message_text(
        "شبکه مورد نظر را انتخاب کنید:",
        reply_markup=NETWORK_KEYBOARDS[currency],
    )
    return GET_NETWORK


# ---------------------------------------------------------------------------
# Step 4 — receive network (callback)
# ---------------------------------------------------------------------------
async def get_network(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    network = query.data
    context.user_data["network"] = network

    await query.edit_message_text(
        "⚠️ توجه: ما ۵٪ کارمزد از مبلغ اضافه می‌کنیم.\n"
        "لطفاً مبلغ مورد نظر به تومان را وارد کنید:"
    )
    return GET_AMOUNT


# ---------------------------------------------------------------------------
# Step 5 — receive amount
# ---------------------------------------------------------------------------
async def get_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        amount = parse_amount(update.message.text)
    except (ValueError, AttributeError):
        await update.message.reply_text(
            "❌ مبلغ وارد شده معتبر نیست.\n"
            "لطفاً یک عدد مثبت وارد کنید (مثال: ۵۰۰۰۰۰۰ یا 5000000):"
        )
        return GET_AMOUNT

    final_amount   = amount * 1.05
    payment_amount = randomize_amount(final_amount)
    context.user_data["amount"]         = amount
    context.user_data["final_amount"]   = final_amount
    context.user_data["payment_amount"] = payment_amount

    await update.message.reply_text(
        f"لطفاً مبلغ <b>{format_amount(payment_amount)} تومان</b> را به شماره کارت زیر واریز کنید:\n\n"
        "<code>6219861936033249</code>\n"
        "قاسمی وند\n\n"
        "⚡️ برای تسریع در فرآیند تأیید رسید، لطفاً همین مبلغ را <b>دقیقاً</b> واریز کنید.\n"
        "مبالغ غیر رند، پردازش سریع‌تری دارند.\n\n"
        "سپس تصویر یا متن رسید واریزی خود را ارسال کنید.",
        parse_mode="HTML",
    )
    return GET_RECEIPT


# ---------------------------------------------------------------------------
# Step 6 — receive receipt (photo or text)
# ---------------------------------------------------------------------------
async def get_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user

    if update.message.photo:
        context.user_data["receipt_type"]    = "photo"
        context.user_data["receipt_file_id"] = update.message.photo[-1].file_id
    else:
        context.user_data["receipt_type"] = "text"
        context.user_data["receipt_text"] = update.message.text or "(بدون متن)"

    context.user_data["user_id"]  = user.id
    context.user_data["username"] = user.username or str(user.id)

    await update.message.reply_text(
        "✅ رسید شما به ادمین ارسال شد. لطفاً صبور باشید..."
    )

    asyncio.create_task(
        _send_confirmation(
            bot=context.bot,
            chat_id=update.effective_chat.id,
            data=dict(context.user_data),
        )
    )

    return ConversationHandler.END


# ---------------------------------------------------------------------------
# /cancel — works at any step
# ---------------------------------------------------------------------------
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(
        "❌ عملیات لغو شد.",
        reply_markup=MAIN_KEYBOARD,
    )
    return ConversationHandler.END


# ---------------------------------------------------------------------------
# Build the ConversationHandler
# ---------------------------------------------------------------------------
def build_conversation_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            MessageHandler(NEW_REQUEST_FILTER, start),
        ],
        states={
            GET_WALLET: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_wallet),
            ],
            GET_CURRENCY: [
                CallbackQueryHandler(get_currency, pattern="^(USDT|TRX)$"),
            ],
            GET_NETWORK: [
                CallbackQueryHandler(
                    get_network, pattern="^(TRC20|ERC20|BEP20|TRON)$"
                ),
            ],
            GET_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_amount),
            ],
            GET_RECEIPT: [
                MessageHandler(
                    (filters.PHOTO | filters.TEXT) & ~filters.COMMAND,
                    get_receipt,
                ),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("start", start),
            MessageHandler(NEW_REQUEST_FILTER, start),
        ],
        allow_reentry=True,
        per_message=False,
    )
