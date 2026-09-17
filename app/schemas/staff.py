from datetime import date

from pydantic import BaseModel, ConfigDict


class StaffCreate(BaseModel):
    name: str
    role: str
    gender: str
    date_of_birth: date | None = None
    phone: str
    email: str | None = None
    address: str | None = None
    qualification: str | None = None
    experience: str | None = None
    joining_date: date | None = None
    status: str = "Active"


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

    model_config = ConfigDict(
        from_attributes=True
    )