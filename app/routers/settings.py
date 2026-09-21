import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.settings import HospitalSetting
from app.schemas.settings import SettingsResponse, SettingsUpdate

router = APIRouter(
    prefix="/api/settings",
    tags=["Settings"]
)

DEFAULT_SETTINGS = {
    "hospitalName": "CareCore Hospital",
    "registrationNumber": "HSP-KOL-2026-0048",
    "email": "admin@carecore.com",
    "phone": "+91 98765 00000",
    "address": "12 Lake View Road, Salt Lake, Kolkata",
    "website": "www.carecore.com",
    "gstin": "19ABCDE1234F1Z5",
    "logo": "",
    "billingTaxRate": 5,
    "timezone": "Asia/Kolkata",
    "openingTime": "06:00",
    "closingTime": "22:00",
    "appointmentDuration": "30",
    "currency": "INR",
    "emailNotifications": True,
    "smsNotifications": True,
    "emergencyAlerts": True,
    "weeklyReports": False,
    "twoFactor": True,
    "shiftReminders": True,
    "taskAlerts": True,
    "theme": "light",
}


@router.get("", response_model=SettingsResponse)
def get_settings(db: Session = Depends(get_db)):
    rows = db.query(HospitalSetting).all()
    current = dict(DEFAULT_SETTINGS)

    for row in rows:
        try:
            val = json.loads(row.value)
        except Exception:
            val = row.value
        current[row.key] = val

    return {"settings": current}


@router.put("", response_model=SettingsResponse)
def update_settings(data: SettingsUpdate, db: Session = Depends(get_db)):
    for key, value in data.settings.items():
        row = db.query(HospitalSetting).filter(HospitalSetting.key == key).first()
        serialized = json.dumps(value) if not isinstance(value, str) else value
        if row:
            row.value = serialized
        else:
            row = HospitalSetting(key=key, value=serialized)
            db.add(row)

    db.commit()

    rows = db.query(HospitalSetting).all()
    current = dict(DEFAULT_SETTINGS)
    for r in rows:
        try:
            val = json.loads(r.value)
        except Exception:
            val = r.value
        current[r.key] = val

    return {"settings": current}
