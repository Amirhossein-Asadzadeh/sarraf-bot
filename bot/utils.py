import random
from datetime import datetime
from zoneinfo import ZoneInfo

TEHRAN_TZ = ZoneInfo("Asia/Tehran")

_PERSIAN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")


def persian_to_english(text: str) -> str:
    """Convert Persian/Arabic-Indic digit characters to ASCII digits."""
    return text.translate(_PERSIAN_DIGITS)


def parse_amount(text: str) -> float:
    """
    Parse a user-provided amount string that may contain:
    - Persian/Arabic digits
    - Comma separators (both , and ،)
    Returns a positive float, or raises ValueError.
    """
    text = persian_to_english(text)
    text = text.replace("،", "").replace(",", "").strip()
    value = float(text)
    if value <= 0:
        raise ValueError("amount must be positive")
    return value


def format_amount(value: float) -> str:
    """Format a number with thousand-separators and no decimals."""
    return f"{value:,.0f}"


def randomize_amount(amount: float) -> int:
    """
    Apply a random ±5% variation so every transaction has a unique non-round amount.
    Returns an integer (toman has no sub-unit worth tracking).
    """
    factor = random.uniform(0.95, 1.05)
    return round(amount * factor)


def tehran_now_str() -> str:
    """Return current Tehran time as  HH:MM - YYYY/MM/DD."""
    now = datetime.now(TEHRAN_TZ)
    return now.strftime("%H:%M - %Y/%m/%d")
