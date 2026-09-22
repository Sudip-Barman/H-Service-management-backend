from datetime import date, datetime
from sqlalchemy import Boolean, Date, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class FollowUp(Base):
    __tablename__ = "follow_ups"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True
    )

    follow_up_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False
    )

    name: Mapped[str] = mapped_column(
        String(100),
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

    patient_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True
    )

    relation: Mapped[str | None] = mapped_column(
        String(50),
        default="Self",
        nullable=True
    )

    source: Mapped[str | None] = mapped_column(
        String(50),
        default="Phone Call",
        nullable=True
    )

    followup_type: Mapped[str] = mapped_column(
        String(100),
        default="Medical Follow Up",
        nullable=False
    )

    query: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    priority: Mapped[str] = mapped_column(
        String(20),
        default="Medium",
        nullable=False
    )

    follow_up_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    assigned_to: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    next_action: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="Follow-up Required",
        nullable=False
    )

    notification_sent: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    triggered_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    last_notification_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True
    )

    is_recurring: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    recurrence_interval: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    recurrence_end_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

