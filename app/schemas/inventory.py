from datetime import date
from pydantic import BaseModel, ConfigDict, field_validator


class InventoryCreate(BaseModel):
    code: str
    name: str
    category: str
    item_type: str | None = None
    unit: str = "Unit"
    quantity: int = 0
    minimum: int = 10
    maximum: int | None = None
    price: float = 0.0
    supplier: str | None = None
    batch: str | None = None
    manufacture: date | None = None
    expiry: date | None = None
    location: str | None = None
    item_condition: str | None = "Good"
    status: str = "Available"

    @field_validator("manufacture", "expiry", mode="before")
    @classmethod
    def empty_str_to_none_date(cls, v):
        if v == "" or v is None:
            return None
        return v

    @field_validator("quantity", "minimum", "maximum", "price", mode="before")
    @classmethod
    def empty_str_to_numeric(cls, v):
        if v == "" or v is None:
            return 0
        return v


class InventoryUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    item_type: str | None = None
    unit: str | None = None
    quantity: int | None = None
    minimum: int | None = None
    maximum: int | None = None
    price: float | None = None
    supplier: str | None = None
    batch: str | None = None
    manufacture: date | None = None
    expiry: date | None = None
    location: str | None = None
    item_condition: str | None = None
    status: str | None = None

    @field_validator("manufacture", "expiry", mode="before")
    @classmethod
    def empty_str_to_none_date(cls, v):
        if v == "" or v is None:
            return None
        return v

    @field_validator("quantity", "minimum", "maximum", "price", mode="before")
    @classmethod
    def empty_str_to_numeric(cls, v):
        if v == "" or v is None:
            return None
        return v


class InventoryResponse(BaseModel):
    id: int
    code: str
    name: str
    category: str
    item_type: str | None
    unit: str
    quantity: int
    minimum: int
    maximum: int | None
    price: float
    supplier: str | None
    batch: str | None
    manufacture: date | None
    expiry: date | None
    location: str | None
    item_condition: str | None
    status: str

    model_config = ConfigDict(from_attributes=True)
