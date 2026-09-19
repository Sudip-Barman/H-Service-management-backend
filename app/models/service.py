from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    price: Mapped[float] = mapped_column(
        nullable=False,
        default=0
    )
    staff_required: Mapped[int] = mapped_column(
        nullable=False,
        default=1
    )
    available_staff: Mapped[int] = mapped_column(
        nullable=False,
        default=0
    )
    bookings: Mapped[int] = mapped_column(
        nullable=False,
        default=0
    )
    rating: Mapped[float] = mapped_column(
        nullable=False,
        default=0
    )
    duration: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True
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