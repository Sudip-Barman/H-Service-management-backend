from datetime import date, datetime, time
from sqlalchemy import Date, DateTime, Integer, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Admission(Base):
    __tablename__ = "admissions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True
    )

    admission_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False
    )

    patient_id: Mapped[int] = mapped_column(
        Integer,
        index=True,
        nullable=False
    )

    doctor_id: Mapped[int] = mapped_column(
        Integer,
        index=True,
        nullable=False
    )

    room_bed_id: Mapped[int | None] = mapped_column(
        Integer,
        index=True,
        nullable=True
    )

    admission_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    admission_time: Mapped[time | None] = mapped_column(
        Time,
        nullable=True
    )

    admission_type: Mapped[str] = mapped_column(
        String(50),
        default="Planned",
        nullable=False
    )

    reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    diagnosis: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    discharge_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True
    )

    discharge_time: Mapped[time | None] = mapped_column(
        Time,
        nullable=True
    )

    discharge_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    discharge_status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="Admitted",
        nullable=False,
        index=True
    )

    remarks: Mapped[str | None] = mapped_column(
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
