from datetime import date, datetime
from sqlalchemy import Date, DateTime, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True
    )

    code: Mapped[str] = mapped_column(
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
        nullable=False
    )

    item_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    unit: Mapped[str] = mapped_column(
        String(50),
        default="Unit",
        nullable=False
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    minimum: Mapped[int] = mapped_column(
        Integer,
        default=10,
        nullable=False
    )

    maximum: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    price: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=0.0,
        nullable=False
    )

    supplier: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True
    )

    batch: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    manufacture: Mapped[date | None] = mapped_column(
        Date,
        nullable=True
    )

    expiry: Mapped[date | None] = mapped_column(
        Date,
        nullable=True
    )

    location: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    item_condition: Mapped[str | None] = mapped_column(
        String(50),
        default="Good",
        nullable=True
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
