from datetime import date, datetime
from sqlalchemy import Date, DateTime, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Bill(Base):
    __tablename__ = "bills"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True
    )

    invoice_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False
    )

    patient_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True
    )

    patient_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    patient_age: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True
    )

    patient_gender: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True
    )

    patient_phone: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True
    )

    patient_email: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True
    )

    address: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    bill_type: Mapped[str] = mapped_column(
        String(50),
        default="Patient",
        nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    doctor: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    department: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    subtotal: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=0.0,
        nullable=False
    )

    tax: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=0.0,
        nullable=False
    )

    discount: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=0.0,
        nullable=False
    )

    total_amount: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=0.0,
        nullable=False
    )

    paid_amount: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=0.0,
        nullable=False
    )

    payment_status: Mapped[str] = mapped_column(
        String(30),
        default="Pending",
        nullable=False
    )

    payment_method: Mapped[str | None] = mapped_column(
        String(50),
        default="Cash",
        nullable=True
    )

    items_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    source: Mapped[str] = mapped_column(
        String(20),
        default="booking",
        nullable=False
    )

    booking_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )
