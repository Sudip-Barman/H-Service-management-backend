from datetime import date
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

    model_config = ConfigDict(from_attributes=True)
