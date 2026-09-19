from datetime import date as dt_date
from pydantic import BaseModel, ConfigDict


class ShiftCreate(BaseModel):
    shift_code: str | None = None
    staff_id: int | None = None
    staff_name: str
    employee_id: str | None = None
    department: str
    date: dt_date
    shift: str = "Morning"
    start_time: str
    end_time: str
    location: str | None = None
    status: str = "Scheduled"
    notes: str | None = None


class ShiftUpdate(BaseModel):
    staff_name: str | None = None
    employee_id: str | None = None
    department: str | None = None
    date: dt_date | None = None
    shift: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    location: str | None = None
    status: str | None = None
    notes: str | None = None


class ShiftResponse(BaseModel):
    id: int
    shift_code: str | None = None
    staff_id: int | None = None
    staff_name: str
    employee_id: str | None = None
    department: str
    date: dt_date
    shift: str
    start_time: str
    end_time: str
    location: str | None = None
    status: str
    notes: str | None = None

    model_config = ConfigDict(from_attributes=True)
