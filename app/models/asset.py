from datetime import datetime
from sqlalchemy import DateTime, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class HospitalAsset(Base):
    __tablename__ = "hospital_assets"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True
    )

    asset_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True
    )

    category: Mapped[str] = mapped_column(
        String(100),
        default="Medical Equipment",
        nullable=False
    )

    department: Mapped[str] = mapped_column(
        String(100),
        default="General Ward",
        nullable=False
    )

    model_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    serial_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    location: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True
    )

    purchase_cost: Mapped[float] = mapped_column(
        Numeric(12, 2),
        default=0.0,
        nullable=False
    )

    purchase_date: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    warranty_expiry: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    next_maintenance: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    assigned_to: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    condition: Mapped[str] = mapped_column(
        String(50),
        default="Good",
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="Operational",
        nullable=False
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
