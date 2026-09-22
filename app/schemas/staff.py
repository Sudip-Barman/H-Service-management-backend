from datetime import date

from pydantic import BaseModel, ConfigDict, field_validator
from app.utils.validation import validate_phone_number


class StaffCreate(BaseModel):
    name: str
    role: str = "Staff"
    gender: str | None = "Male"
    date_of_birth: date | None = None
    phone: str
    email: str | None = None
    address: str | None = None
    qualification: str | None = None
    experience: str | None = None
    joining_date: date | None = None
    status: str = "Active"
    username: str | None = None
    temporary_password: str | None = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        return validate_phone_number(v, "Phone number")

    @field_validator("date_of_birth", "joining_date", mode="before")
    @classmethod
    def empty_str_to_none_date(cls, v):
        if v == "" or v is None:
            return None
        return v

    @field_validator("date_of_birth")
    @classmethod
    def validate_staff_dob(cls, v: date | None) -> date | None:
        if v and v > date.today():
            raise ValueError("Date of Birth cannot be greater than today's date.")
        return v


class StaffUpdate(BaseModel):
    name: str | None = None
    role: str | None = None
    gender: str | None = None
    date_of_birth: date | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    qualification: str | None = None
    experience: str | None = None
    joining_date: date | None = None
    status: str | None = None
    username: str | None = None
    temporary_password: str | None = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        if v is not None:
            return validate_phone_number(v, "Phone number")
        return None

    @field_validator("date_of_birth", "joining_date", mode="before")
    @classmethod
    def empty_str_to_none_date(cls, v):
        if v == "" or v is None:
            return None
        return v

    @field_validator("date_of_birth")
    @classmethod
    def validate_staff_dob(cls, v: date | None) -> date | None:
        if v and v > date.today():
            raise ValueError("Date of Birth cannot be greater than today's date.")
        return v


class StaffResponse(BaseModel):
    id: int
    name: str
    role: str
    gender: str
    date_of_birth: date | None
    phone: str
    email: str | None
    address: str | None
    qualification: str | None
    experience: str | None
    joining_date: date | None
    status: str
    user_id: int | None = None
    username: str | None = None
    temporary_password: str | None = None

    model_config = ConfigDict(
        from_attributes=True
    )