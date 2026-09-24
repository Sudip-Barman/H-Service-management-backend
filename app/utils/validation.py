import json
import re
from datetime import date
from sqlalchemy.orm import Session

from app.models.settings import HospitalSetting
from app.routers.settings import DEFAULT_SETTINGS


def validate_phone_number(phone: str, field_name: str = "Phone number") -> str:
    """
    Validates that a phone number contains exactly 10 digits (0-9 only).
    Does not allow letters, spaces, or special characters.
    """
    if phone is None:
        raise ValueError(f"{field_name} must contain exactly 10 digits.")

    cleaned = str(phone).strip()

    # Digits only and exactly 10 characters
    if not re.match(r"^\d{10}$", cleaned):
        raise ValueError(f"{field_name} must contain exactly 10 digits.")

    return cleaned


def get_age_from_dob(dob: date) -> int:
    """
    Accurately computes current age in full years from a date of birth.
    """
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def get_hospital_settings(db: Session | None = None) -> dict:
    """
    Retrieves current hospital settings from database or falls back to defaults.
    """
    settings = dict(DEFAULT_SETTINGS)
    if db is not None:
        try:
            rows = db.query(HospitalSetting).all()
            for r in rows:
                try:
                    val = json.loads(r.value)
                except Exception:
                    val = r.value
                settings[r.key] = val
        except Exception:
            pass
    return settings


def validate_dob(
    dob: date | None,
    is_staff: bool = False,
    db: Session | None = None,
    min_age: int | None = None,
    max_age: int | None = None,
) -> date | None:
    """
    Validates that DOB is not in the future and strictly respects age limits.
    """
    if dob is None:
        return None

    today = date.today()
    if dob > today:
        raise ValueError("Date of Birth cannot be greater than today's date.")

    age = get_age_from_dob(dob)

    if min_age is None or max_age is None:
        settings = get_hospital_settings(db)
        if is_staff:
            min_age = int(settings.get("minStaffAge", 18))
            max_age = int(settings.get("maxStaffAge", 75))
        else:
            min_age = int(settings.get("minPatientAge", settings.get("minAge", 0)))
            max_age = int(settings.get("maxPatientAge", settings.get("maxAge", 125)))

    if age < min_age or age > max_age:
        if is_staff:
            raise ValueError(f"Staff age must be between {min_age} and {max_age} years.")
        else:
            raise ValueError(f"Patient age must be between {min_age} and {max_age} years.")

    return dob

