from datetime import date, datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")


def get_current_ist_datetime() -> datetime:
    """Returns the current date and time in Asia/Kolkata timezone."""
    return datetime.now(IST)


def get_current_ist_date() -> date:
    """Returns the current calendar date in Asia/Kolkata timezone."""
    return datetime.now(IST).date()
