from datetime import datetime
from pydantic import BaseModel, Field


class AssetBase(BaseModel):
    asset_code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=150)
    category: str = Field(default="Medical Equipment", max_length=100)
    department: str = Field(default="General Ward", max_length=100)
    model_number: str | None = Field(default=None, max_length=100)
    serial_number: str | None = Field(default=None, max_length=100)
    location: str | None = Field(default=None, max_length=150)
    purchase_cost: float = Field(default=0.0, ge=0)
    purchase_date: str | None = None
    warranty_expiry: str | None = None
    next_maintenance: str | None = None
    assigned_to: str | None = Field(default=None, max_length=100)
    condition: str = Field(default="Good", max_length=50)
    status: str = Field(default="Operational", max_length=50)
    notes: str | None = None


class AssetCreate(AssetBase):
    pass


class AssetUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    department: str | None = None
    model_number: str | None = None
    serial_number: str | None = None
    location: str | None = None
    purchase_cost: float | None = None
    purchase_date: str | None = None
    warranty_expiry: str | None = None
    next_maintenance: str | None = None
    assigned_to: str | None = None
    condition: str | None = None
    status: str | None = None
    notes: str | None = None


class AssetResponse(AssetBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
