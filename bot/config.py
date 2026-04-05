import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root (one level above bot/)
load_dotenv(Path(__file__).parent.parent / ".env")

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "marjanghaffarzadeh")

# Admin must send /start to the bot once; then place their numeric chat ID here.
# Run:  python -c "from bot.utils import get_admin_id; ..."
# Or watch the bot logs on first /start from admin account.
_admin_chat_id_env = os.getenv("ADMIN_CHAT_ID", "0")
ADMIN_CHAT_ID: int = int(_admin_chat_id_env) if _admin_chat_id_env.isdigit() else 0

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set. Add it to .env or environment variables.")
