from datetime import date, datetime
from sqlalchemy import Date, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Schedule(Base):
    __tablename__ = "schedules"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True
    )

    doctor_id: Mapped[int | None] = mapped_column(
        Integer,
        index=True,
        nullable=True
    )

    doctor_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    department: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True
    )

    start_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True
    )

    end_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True
    )

    start_time: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    end_time: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    location: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    type: Mapped[str] = mapped_column(
        String(50),
        default="Consultation",
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
