from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True
    )

    room_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False
    )

    ward: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    room_type: Mapped[str] = mapped_column(
        String(50),
        default="General",
        nullable=False
    )

    floor: Mapped[str] = mapped_column(
        String(50),
        default="1st Floor",
        nullable=False
    )

    department: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    daily_charge: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=500.00,
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="Active",
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    beds: Mapped[list["Bed"]] = relationship(
        "Bed",
        back_populates="room",
        cascade="all, delete-orphan"
    )


class Bed(Base):
    __tablename__ = "beds"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True
    )

    room_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    bed_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="Available",
        nullable=False,
        index=True
    )

    patient_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True
    )

    patient_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    patient_code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    admission_date: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    daily_charge: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=500.00,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    room: Mapped["Room"] = relationship("Room", back_populates="beds")
