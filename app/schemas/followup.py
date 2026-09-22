from datetime import date, datetime
from pydantic import BaseModel, ConfigDict


class FollowUpCreate(BaseModel):
    follow_up_code: str
    name: str
    phone: str
    email: str | None = None
    patient_id: str | None = None
    relation: str | None = "Self"
    source: str | None = "Phone Call"
    followup_type: str = "Medical Follow Up"
    query: str | None = None
    priority: str = "Medium"
    follow_up_date: date
    assigned_to: str | None = None
    notes: str | None = None
    next_action: str | None = None
    status: str = "Follow-up Required"
    is_recurring: bool = False
    recurrence_interval: str | None = None
    recurrence_end_date: date | None = None


class FollowUpUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    email: str | None = None
    patient_id: str | None = None
    relation: str | None = None
    source: str | None = None
    followup_type: str | None = None
    query: str | None = None
    priority: str | None = None
    follow_up_date: date | None = None
    assigned_to: str | None = None
    notes: str | None = None
    next_action: str | None = None
    status: str | None = None
    notification_sent: bool | None = None
    is_recurring: bool | None = None
    recurrence_interval: str | None = None
    recurrence_end_date: date | None = None


class FollowUpResponse(BaseModel):
    id: int
    follow_up_code: str
    name: str
    phone: str
    email: str | None
    patient_id: str | None
    relation: str | None
    source: str | None
    followup_type: str
    query: str | None
    priority: str
    follow_up_date: date
    assigned_to: str | None
    notes: str | None
    next_action: str | None
    status: str
    notification_sent: bool = False
    triggered_at: datetime | None = None
    last_notification_date: date | None = None
    is_recurring: bool = False
    recurrence_interval: str | None = None
    recurrence_end_date: date | None = None

    model_config = ConfigDict(from_attributes=True)

