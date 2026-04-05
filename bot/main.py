"""
Entry point — builds and runs the Telegram bot application.
"""

import logging
import warnings

from telegram.warnings import PTBUserWarning

warnings.filterwarnings("ignore", category=PTBUserWarning)

from telegram import Update
from telegram.error import NetworkError, TimedOut
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

from .config import BOT_TOKEN
from .handlers import MAIN_KEYBOARD, build_conversation_handler

logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    if isinstance(context.error, (TimedOut, NetworkError)):
        logger.warning("Network error (will retry automatically): %s", context.error)
        return
    logger.exception("Unhandled exception", exc_info=context.error)


def main() -> None:
    logger.info("Starting sarraf bot…")

    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .connect_timeout(30)
        .read_timeout(30)
        .write_timeout(30)
        .pool_timeout(30)
        .build()
    )

    # Show the main keyboard to any user who sends a message before /start
    async def greet_new_user(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text(
            "سلام! برای شروع روی دکمه زیر ضربه بزنید 👇",
            reply_markup=MAIN_KEYBOARD,
        )

    app.add_handler(build_conversation_handler())
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, greet_new_user))
    app.add_error_handler(error_handler)

    logger.info("Polling for updates…")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
