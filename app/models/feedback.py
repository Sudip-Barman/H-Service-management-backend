from datetime import datetime
from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Feedback(Base):
    __tablename__ = "feedbacks"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True
    )

    feedback_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False
    )

    patient: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    email: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True
    )

    service: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    rating: Mapped[int] = mapped_column(
        Integer,
        default=5,
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="New",
        nullable=False
    )

    date: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    comment: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )
