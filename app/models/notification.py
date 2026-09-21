from datetime import datetime
from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True
    )

    title: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    type: Mapped[str] = mapped_column(
        String(50),
        default="General",
        nullable=False
    )

    priority: Mapped[str] = mapped_column(
        String(20),
        default="Normal",
        nullable=False
    )

    department: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    recipient: Mapped[str | None] = mapped_column(
        String(100),
        default="All Clinical Staff",
        nullable=True
    )

    date: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True
    )

    time: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True
    )

    read: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    recipient_user_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True
    )

    recipient_role: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True
    )

    related_entity_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True
    )

    related_entity_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    action_url: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )
