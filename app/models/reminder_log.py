from datetime import datetime
from sqlalchemy import DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ReminderNotificationLog(Base):
    __tablename__ = "reminder_notification_logs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True
    )

    reminder_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )

    reminder_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True
    )

    occurrence_date: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True
    )

    recipient_key: Mapped[str] = mapped_column(
        String(100),
        default="admin",
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    __table_args__ = (
        UniqueConstraint(
            "reminder_type",
            "reminder_id",
            "occurrence_date",
            "recipient_key",
            name="uq_reminder_occurrence_recipient"
        ),
    )
