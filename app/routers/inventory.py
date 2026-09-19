from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.inventory import InventoryItem
from app.schemas.inventory import InventoryCreate, InventoryResponse, InventoryUpdate

router = APIRouter(
    prefix="/api/inventory",
    tags=["Inventory"]
)


def _format_inventory(item: InventoryItem) -> dict:
    return {
        "id": item.id,
        "code": item.code,
        "name": item.name,
        "category": item.category,
        "type": item.item_type or "General",
        "unit": item.unit,
        "quantity": item.quantity,
        "minimum": item.minimum,
        "maximum": item.maximum or (item.minimum * 10),
        "price": float(item.price),
        "supplier": item.supplier or "Hospital Central Supply",
        "batch": item.batch or f"BATCH-{item.id:04d}",
        "manufacture": str(item.manufacture) if item.manufacture else "",
        "expiry": str(item.expiry) if item.expiry else "",
        "location": item.location or "Store Room A",
        "condition": item.item_condition or "Good",
        "status": item.status,
    }


@router.get("")
def get_inventory_items(db: Session = Depends(get_db)):
    items = db.query(InventoryItem).order_by(InventoryItem.name.asc()).all()
    return [_format_inventory(i) for i in items]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_inventory_item(data: InventoryCreate, db: Session = Depends(get_db)):
    existing = db.query(InventoryItem).filter(InventoryItem.code == data.code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Item code already exists"
        )

    status_val = data.status
    if data.quantity <= 0:
        status_val = "Out of Stock"
    elif data.quantity <= data.minimum:
        status_val = "Low Stock"
    else:
        status_val = "Available"

    item = InventoryItem(**data.model_dump())
    item.status = status_val
    db.add(item)
    db.commit()
    db.refresh(item)
    return _format_inventory(item)


@router.put("/{item_id}")
def update_inventory_item(item_id: int, data: InventoryUpdate, db: Session = Depends(get_db)):
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory item not found"
        )

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(item, field, value)

    if item.quantity <= 0:
        item.status = "Out of Stock"
    elif item.quantity <= item.minimum:
        item.status = "Low Stock"
    else:
        item.status = "Available"

    db.commit()
    db.refresh(item)
    return _format_inventory(item)


@router.delete("/{item_id}")
def delete_inventory_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory item not found"
        )

    db.delete(item)
    db.commit()
    return {"message": "Inventory item deleted successfully"}
