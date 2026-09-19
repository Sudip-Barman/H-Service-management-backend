from datetime import date, datetime
from sqlalchemy import Date, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Attendance(Base):
    __tablename__ = "attendance"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True
    )

    staff_id: Mapped[int | None] = mapped_column(
        Integer,
        index=True,
        nullable=True
    )

    employee_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    staff_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    role: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    department: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True
    )

    shift: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    check_in: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True
    )

    check_out: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="Present",
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )
