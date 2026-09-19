from datetime import date, datetime
from sqlalchemy import Date, DateTime, Integer, String, Text
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Nurse(Base):
    __tablename__ = "nurses"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True
    )

    nurse_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True
    )

    staff_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True
    )

    registration_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False
    )

    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    middle_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    last_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    date_of_birth: Mapped[date | None] = mapped_column(
        Date,
        nullable=True
    )

    gender: Mapped[str] = mapped_column(
        String(20),
        default="Female",
        nullable=False
    )

    phone: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    email: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True
    )

    address: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    qualification: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True
    )

    department: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    ward: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    experience_years: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    license_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    license_expiry: Mapped[date | None] = mapped_column(
        Date,
        nullable=True
    )

    shift_type: Mapped[str] = mapped_column(
        String(50),
        default="Morning",
        nullable=False
    )

    photo: Mapped[str | None] = mapped_column(
        Text().with_variant(LONGTEXT, "mysql"),
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="Active",
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
