from datetime import date, datetime
from sqlalchemy import Date, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class BloodStock(Base):
    __tablename__ = "blood_stocks"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True
    )

    blood_group: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        index=True
    )

    component: Mapped[str] = mapped_column(
        String(50),
        default="Whole Blood",
        nullable=False
    )

    units: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    min_stock: Mapped[int] = mapped_column(
        Integer,
        default=10,
        nullable=False
    )

    expiry_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True
    )

    donor_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="Available",
        nullable=False
    )

    location: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
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
