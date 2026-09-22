from datetime import date
from pydantic import BaseModel, ConfigDict, field_validator
from app.utils.validation import validate_phone_number


class DoctorCreate(BaseModel):
    registration_number: str
    first_name: str
    middle_name: str | None = None
    last_name: str | None = None
    date_of_birth: date | None = None
    gender: str = "Male"
    phone: str
    email: str | None = None
    address: str | None = None
    specialization: str
    department: str
    qualification: str | None = None
    experience_years: int = 0
    consultation_fee: float = 0.0
    license_number: str | None = None
    license_expiry: date | None = None
    available_status: str = "Available"
    status: str = "Active"

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        return validate_phone_number(v, "Phone number")

    @field_validator("date_of_birth", "license_expiry", mode="before")
    @classmethod
    def empty_str_to_none_date(cls, v):
        if v == "" or v is None:
            return None
        return v

    @field_validator("date_of_birth")
    @classmethod
    def validate_doctor_dob(cls, v: date | None) -> date | None:
        if v and v > date.today():
            raise ValueError("Date of Birth cannot be greater than today's date.")
        return v

    @field_validator("experience_years", "consultation_fee", mode="before")
    @classmethod
    def empty_str_to_numeric(cls, v):
        if v == "" or v is None:
            return 0
        return v


class DoctorUpdate(BaseModel):
    registration_number: str | None = None
    first_name: str | None = None
    middle_name: str | None = None
    last_name: str | None = None
    date_of_birth: date | None = None
    gender: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    specialization: str | None = None
    department: str | None = None
    qualification: str | None = None
    experience_years: int | None = None
    consultation_fee: float | None = None
    license_number: str | None = None
    license_expiry: date | None = None
    available_status: str | None = None
    status: str | None = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        if v is not None:
            return validate_phone_number(v, "Phone number")
        return None

    @field_validator("date_of_birth", "license_expiry", mode="before")
    @classmethod
    def empty_str_to_none_date(cls, v):
        if v == "" or v is None:
            return None
        return v

    @field_validator("date_of_birth")
    @classmethod
    def validate_doctor_dob(cls, v: date | None) -> date | None:
        if v and v > date.today():
            raise ValueError("Date of Birth cannot be greater than today's date.")
        return v

    @field_validator("experience_years", "consultation_fee", mode="before")
    @classmethod
    def empty_str_to_numeric(cls, v):
        if v == "" or v is None:
            return None
        return v


class DoctorResponse(BaseModel):
    id: int
    registration_number: str
    first_name: str
    middle_name: str | None
    last_name: str | None
    date_of_birth: date | None
    gender: str
    phone: str
    email: str | None
    address: str | None
    specialization: str
    department: str
    qualification: str | None
    experience_years: int
    consultation_fee: float
    license_number: str | None
    license_expiry: date | None
    photo: str | None
    available_status: str
    status: str
    user_id: int | None = None
    username: str | None = None
    temporary_password: str | None = None

    model_config = ConfigDict(from_attributes=True)