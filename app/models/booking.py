from datetime import date, datetime, time

from sqlalchemy import Date, DateTime, Integer, Numeric, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Booking(Base):
    __tablename__ = "bookings"

    booking_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    booking_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    patient_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
    )

    doctor_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
    )

    service_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
    )

    booking_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    booking_time: Mapped[time | None] = mapped_column(
        Time,
        nullable=True,
    )

    booking_category: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        default="Checkup / Consultation",
    )

    patient_type: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    patient_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    patient_phone: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    patient_email: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    patient_address: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    assigned_staff_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    service_duration: Mapped[float | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )

    service_duration_unit: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    service_start_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    service_end_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    service_rate: Mapped[float | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )

    service_pricing_type: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    total_fee: Mapped[float | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )

    service_location_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    service_address: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    service_area: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    service_city: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    service_pincode: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    service_landmark: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    booking_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="In-Person",
    )

    priority: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="Normal",
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="Scheduled",
        index=True,
    )

    consultation_fee: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=0,
    )

    payment_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="Pending",
    )

    reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_by: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )