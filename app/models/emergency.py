from datetime import datetime
from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class EmergencyPatient(Base):
    __tablename__ = "emergency_patients"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True
    )

    emergency_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    age: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True
    )

    gender: Mapped[str] = mapped_column(
        String(20),
        default="Male",
        nullable=False
    )

    blood_group: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True
    )

    phone: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True
    )

    emergency_contact: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    emergency_phone: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True
    )

    arrival_time: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    triage: Mapped[str] = mapped_column(
        String(30),
        default="Urgent",
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="Under Treatment",
        nullable=False
    )

    condition_summary: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    symptoms: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    assigned_doctor: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    department: Mapped[str | None] = mapped_column(
        String(100),
        default="Emergency Medicine",
        nullable=True
    )

    room: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    allergies: Mapped[str | None] = mapped_column(
        String(255),
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
