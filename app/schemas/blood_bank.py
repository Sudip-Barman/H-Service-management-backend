from datetime import date
from pydantic import BaseModel, ConfigDict


class BloodStockCreate(BaseModel):
    blood_group: str
    component: str = "Whole Blood"
    units: int = 0
    min_stock: int = 10
    expiry_date: date | None = None
    donor_count: int = 0
    status: str = "Available"
    location: str | None = None
    notes: str | None = None


class BloodStockUpdate(BaseModel):
    blood_group: str | None = None
    component: str | None = None
    units: int | None = None
    min_stock: int | None = None
    expiry_date: date | None = None
    donor_count: int | None = None
    status: str | None = None
    location: str | None = None
    notes: str | None = None


class BloodStockResponse(BaseModel):
    id: int
    blood_group: str
    component: str
    units: int
    min_stock: int
    expiry_date: date | None
    donor_count: int
    status: str
    location: str | None
    notes: str | None

    model_config = ConfigDict(from_attributes=True)
