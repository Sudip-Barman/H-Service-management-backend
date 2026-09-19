from datetime import date, datetime
from sqlalchemy import Boolean, Date, DateTime, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Medicine(Base):
    __tablename__ = "medicines"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True
    )

    medicine_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False
    )

    medicine_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True
    )

    generic_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True
    )

    medicine_type: Mapped[str] = mapped_column(
        String(50),
        default="Tablet",
        nullable=False
    )

    category: Mapped[str] = mapped_column(
        String(100),
        default="General",
        nullable=False
    )

    manufacturer: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    batch_number: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    dosage: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    unit: Mapped[str] = mapped_column(
        String(30),
        default="Tablet",
        nullable=False
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    reorder_level: Mapped[int] = mapped_column(
        Integer,
        default=20,
        nullable=False
    )

    purchase_price: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=0.0,
        nullable=False
    )

    selling_price: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=0.0,
        nullable=False
    )

    manufacture_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True
    )

    expiry_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True
    )

    storage_location: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    prescription_required: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="Available",
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
