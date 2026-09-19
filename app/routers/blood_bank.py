from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.blood_bank import BloodStock
from app.schemas.blood_bank import BloodStockCreate, BloodStockResponse, BloodStockUpdate

router = APIRouter(
    prefix="/api/blood-bank",
    tags=["Blood Bank"]
)


def _format_blood_stock(b: BloodStock) -> dict:
    return {
        "id": f"BL-{1000 + b.id}",
        "stock_id": b.id,
        "bloodGroup": b.blood_group,
        "blood_group": b.blood_group,
        "component": b.component,
        "units": b.units,
        "minStock": b.min_stock,
        "min_stock": b.min_stock,
        "expiryDate": str(b.expiry_date) if b.expiry_date else "",
        "expiry_date": str(b.expiry_date) if b.expiry_date else "",
        "donorCount": b.donor_count,
        "donor_count": b.donor_count,
        "status": b.status,
        "location": b.location or "Blood Bank - Main",
        "notes": b.notes,
    }


@router.get("")
def get_blood_stocks(db: Session = Depends(get_db)):
    stocks = db.query(BloodStock).order_by(BloodStock.blood_group.asc()).all()
    return [_format_blood_stock(s) for s in stocks]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_blood_stock(data: BloodStockCreate, db: Session = Depends(get_db)):
    stock = BloodStock(**data.model_dump())
    db.add(stock)
    db.commit()
    db.refresh(stock)
    return _format_blood_stock(stock)


@router.put("/{stock_id}")
def update_blood_stock(stock_id: int, data: BloodStockUpdate, db: Session = Depends(get_db)):
    stock = db.query(BloodStock).filter(BloodStock.id == stock_id).first()
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blood stock record not found"
        )

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(stock, field, value)

    # Automatically compute status from units vs min_stock
    if stock.units <= 0:
        stock.status = "Critical"
    elif stock.units <= stock.min_stock:
        stock.status = "Low Stock"
    else:
        stock.status = "Available"

    db.commit()
    db.refresh(stock)
    return _format_blood_stock(stock)


@router.delete("/{stock_id}")
def delete_blood_stock(stock_id: int, db: Session = Depends(get_db)):
    stock = db.query(BloodStock).filter(BloodStock.id == stock_id).first()
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blood stock record not found"
        )

    db.delete(stock)
    db.commit()
    return {"message": "Blood stock deleted successfully"}
