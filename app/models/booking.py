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

    patient_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )

    doctor_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
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

    booking_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
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