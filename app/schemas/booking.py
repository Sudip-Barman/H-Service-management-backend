from datetime import date, datetime, time
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class BookingBase(BaseModel):
    booking_number: str | None = Field(
        default=None,
        max_length=50,
    )

    patient_id: int
    doctor_id: int
    service_id: int | None = None

    booking_date: date
    booking_time: time

    booking_type: str = Field(
        default="In-Person",
        max_length=30,
    )

    priority: str = Field(
        default="Normal",
        max_length=20,
    )

    status: str = Field(
        default="Scheduled",
        max_length=30,
    )

    consultation_fee: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
    )

    payment_status: str = Field(
        default="Pending",
        max_length=20,
    )

    reason: str | None = None
    notes: str | None = None
    created_by: int | None = None


class BookingCreate(BookingBase):
    pass


class BookingUpdate(BaseModel):
    booking_number: str | None = Field(
        default=None,
        max_length=50,
    )

    patient_id: int | None = None
    doctor_id: int | None = None
    service_id: int | None = None

    booking_date: date | None = None
    booking_time: time | None = None

    booking_type: str | None = Field(
        default=None,
        max_length=30,
    )

    priority: str | None = Field(
        default=None,
        max_length=20,
    )

    status: str | None = Field(
        default=None,
        max_length=30,
    )

    consultation_fee: Decimal | None = Field(
        default=None,
        ge=0,
    )

    payment_status: str | None = Field(
        default=None,
        max_length=20,
    )

    reason: str | None = None
    notes: str | None = None


class BookingStatusUpdate(BaseModel):
    status: str = Field(
        min_length=1,
        max_length=30,
    )


class BookingResponse(BookingBase):
    model_config = ConfigDict(from_attributes=True)

    booking_id: int
    booking_number: str

    created_at: datetime
    updated_at: datetime