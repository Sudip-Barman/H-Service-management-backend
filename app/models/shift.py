from datetime import date, datetime
from sqlalchemy import Date, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class StaffShift(Base):
    __tablename__ = "shifts"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True
    )

    shift_code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    staff_id: Mapped[int | None] = mapped_column(
        Integer,
        index=True,
        nullable=True
    )

    staff_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    employee_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
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

    shift: Mapped[str] = mapped_column(
        String(50),
        default="Morning",
        nullable=False
    )

    start_time: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    end_time: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    location: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="Scheduled",
        nullable=False
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )
