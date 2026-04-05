"""
Entry point — builds and runs the Telegram bot application.
"""

import logging
import warnings

from telegram.warnings import PTBUserWarning

warnings.filterwarnings("ignore", category=PTBUserWarning)

from telegram.ext import ApplicationBuilder

from .config import BOT_TOKEN
from .handlers import build_conversation_handler

logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("Starting sarraf bot…")

    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .build()
    )

    app.add_handler(build_conversation_handler())

    logger.info("Polling for updates…")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
