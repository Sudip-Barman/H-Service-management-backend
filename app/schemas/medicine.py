from datetime import date
from pydantic import BaseModel, ConfigDict, field_validator


class MedicineCreate(BaseModel):
    medicine_code: str
    medicine_name: str
    generic_name: str | None = None
    medicine_type: str = "Tablet"
    category: str = "General"
    manufacturer: str | None = None
    batch_number: str | None = None
    dosage: str | None = None
    unit: str = "Tablet"
    quantity: int = 0
    reorder_level: int = 20
    purchase_price: float = 0.0
    selling_price: float = 0.0
    manufacture_date: date | None = None
    expiry_date: date | None = None
    storage_location: str | None = None
    prescription_required: bool = False
    status: str = "Available"

    @field_validator("manufacture_date", "expiry_date", mode="before")
    @classmethod
    def empty_str_to_none_date(cls, v):
        if v == "" or v is None:
            return None
        return v


class MedicineUpdate(BaseModel):
    medicine_code: str | None = None
    medicine_name: str | None = None
    generic_name: str | None = None
    medicine_type: str | None = None
    category: str | None = None
    manufacturer: str | None = None
    batch_number: str | None = None
    dosage: str | None = None
    unit: str | None = None
    quantity: int | None = None
    reorder_level: int | None = None
    purchase_price: float | None = None
    selling_price: float | None = None
    manufacture_date: date | None = None
    expiry_date: date | None = None
    storage_location: str | None = None
    prescription_required: bool | None = None
    status: str | None = None

    @field_validator("manufacture_date", "expiry_date", mode="before")
    @classmethod
    def empty_str_to_none_date(cls, v):
        if v == "" or v is None:
            return None
        return v


class MedicineResponse(BaseModel):
    id: int
    medicine_code: str
    medicine_name: str
    generic_name: str | None
    medicine_type: str
    category: str
    manufacturer: str | None
    batch_number: str | None
    dosage: str | None
    unit: str
    quantity: int
    reorder_level: int
    purchase_price: float
    selling_price: float
    manufacture_date: date | None
    expiry_date: date | None
    storage_location: str | None
    prescription_required: bool
    status: str

    model_config = ConfigDict(from_attributes=True)
