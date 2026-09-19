from datetime import date, datetime
from sqlalchemy import Date, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class HospitalRequest(Base):
    __tablename__ = "requests"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True
    )

    request_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False
    )

    request_type: Mapped[str] = mapped_column(
        String(50),
        default="Lab Test",
        nullable=False
    )

    item: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    requested_for: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    patient_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True
    )

    requested_by: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    department: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    priority: Mapped[str] = mapped_column(
        String(20),
        default="Normal",
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="Pending",
        nullable=False
    )

    date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    required_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )
