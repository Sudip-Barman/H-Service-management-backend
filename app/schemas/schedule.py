from datetime import date as dt_date
from pydantic import BaseModel, ConfigDict, field_validator


class ScheduleCreate(BaseModel):
    doctor_id: int | None = None
    doctor_name: str
    department: str
    date: dt_date | None = None
    start_date: dt_date | None = None
    end_date: dt_date | None = None
    start_time: str
    end_time: str
    location: str
    type: str = "Consultation"
    status: str = "Available"

    @field_validator("date", "start_date", "end_date", mode="before")
    @classmethod
    def empty_str_to_none_date(cls, v):
        if v == "" or v is None:
            return None
        return v

    @field_validator("doctor_id", mode="before")
    @classmethod
    def empty_str_to_none_int(cls, v):
        if v == "" or v is None:
            return None
        return v


class ScheduleUpdate(BaseModel):
    doctor_id: int | None = None
    doctor_name: str | None = None
    department: str | None = None
    date: dt_date | None = None
    start_date: dt_date | None = None
    end_date: dt_date | None = None
    start_time: str | None = None
    end_time: str | None = None
    location: str | None = None
    type: str | None = None
    status: str | None = None

    @field_validator("date", "start_date", "end_date", mode="before")
    @classmethod
    def empty_str_to_none_date(cls, v):
        if v == "" or v is None:
            return None
        return v

    @field_validator("doctor_id", mode="before")
    @classmethod
    def empty_str_to_none_int(cls, v):
        if v == "" or v is None:
            return None
        return v


class ScheduleResponse(BaseModel):
    id: int
    schedule_id: int | None = None
    doctor_id: int | None = None
    doctor_name: str
    department: str
    date: dt_date
    start_date: dt_date | None = None
    end_date: dt_date | None = None
    start_time: str
    end_time: str
    location: str
    type: str
    status: str

    model_config = ConfigDict(from_attributes=True)
