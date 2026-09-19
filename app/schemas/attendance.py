from datetime import date as dt_date
from pydantic import BaseModel, ConfigDict


class AttendanceCreate(BaseModel):
    staff_id: int | None = None
    employee_id: str | None = None
    staff_name: str
    role: str | None = None
    department: str | None = None
    date: dt_date
    shift: str | None = None
    check_in: str | None = None
    check_out: str | None = None
    status: str = "Present"


class AttendanceUpdate(BaseModel):
    check_in: str | None = None
    check_out: str | None = None
    status: str | None = None
    shift: str | None = None


class AttendanceResponse(BaseModel):
    id: int
    staff_id: int | None = None
    employee_id: str | None = None
    staff_name: str
    role: str | None = None
    department: str | None = None
    date: dt_date
    shift: str | None = None
    check_in: str | None = None
    check_out: str | None = None
    status: str

    model_config = ConfigDict(from_attributes=True)
