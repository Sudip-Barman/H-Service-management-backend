from datetime import date as dt_date
from pydantic import BaseModel, ConfigDict


class RequestCreate(BaseModel):
    request_code: str
    request_type: str = "Lab Test"
    item: str
    requested_for: str | None = None
    patient_id: str | None = None
    requested_by: str
    department: str | None = None
    priority: str = "Normal"
    status: str = "Pending"
    date: dt_date
    required_date: dt_date | None = None
    description: str | None = None


class RequestUpdate(BaseModel):
    request_type: str | None = None
    item: str | None = None
    requested_for: str | None = None
    patient_id: str | None = None
    requested_by: str | None = None
    department: str | None = None
    priority: str | None = None
    status: str | None = None
    date: dt_date | None = None
    required_date: dt_date | None = None
    description: str | None = None


class RequestResponse(BaseModel):
    id: int
    request_code: str
    request_type: str
    item: str
    requested_for: str | None
    patient_id: str | None
    requested_by: str
    department: str | None
    priority: str
    status: str
    date: dt_date
    required_date: dt_date | None
    description: str | None

    model_config = ConfigDict(from_attributes=True)
