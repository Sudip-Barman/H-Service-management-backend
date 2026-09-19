from datetime import date, datetime, time
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class BookingBase(BaseModel):
    booking_number: str | None = Field(
        default=None,
        max_length=50,
    )

    patient_id: int | None = None
    doctor_id: int | None = None
    service_id: int | None = None

    booking_date: date
    booking_time: time | None = None

    booking_category: str | None = "Checkup / Consultation"
    patient_type: str | None = None
    patient_name: str | None = None
    patient_phone: str | None = None
    patient_email: str | None = None
    patient_address: str | None = None

    assigned_staff_id: int | None = None
    service_duration: Decimal | float | None = None
    service_duration_unit: str | None = None
    service_start_date: date | None = None
    service_end_date: date | None = None
    service_rate: Decimal | float | None = None
    service_pricing_type: str | None = None
    total_fee: Decimal | float | None = None

    service_location_type: str | None = None
    service_address: str | None = None
    service_area: str | None = None
    service_city: str | None = None
    service_pincode: str | None = None
    service_landmark: str | None = None

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
    booking_number: str | None = None
    patient_id: int | None = None
    doctor_id: int | None = None
    service_id: int | None = None

    booking_date: date | None = None
    booking_time: time | None = None

    booking_category: str | None = None
    patient_type: str | None = None
    patient_name: str | None = None
    patient_phone: str | None = None
    patient_email: str | None = None
    patient_address: str | None = None

    assigned_staff_id: int | None = None
    service_duration: Decimal | float | None = None
    service_duration_unit: str | None = None
    service_start_date: date | None = None
    service_end_date: date | None = None
    service_rate: Decimal | float | None = None
    service_pricing_type: str | None = None
    total_fee: Decimal | float | None = None

    service_location_type: str | None = None
    service_address: str | None = None
    service_area: str | None = None
    service_city: str | None = None
    service_pincode: str | None = None
    service_landmark: str | None = None

    booking_type: str | None = None
    priority: str | None = None
    status: str | None = None
    consultation_fee: Decimal | None = None
    payment_status: str | None = None
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