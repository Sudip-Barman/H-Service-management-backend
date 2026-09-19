from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.medicine import Medicine
from app.schemas.medicine import MedicineCreate, MedicineResponse, MedicineUpdate

router = APIRouter(
    prefix="/api/medicines",
    tags=["Medicines & Pharmacy"]
)


def _format_medicine(m: Medicine) -> dict:
    return {
        "id": m.id,
        "medicine_id": m.id,
        "medicine_code": m.medicine_code,
        "medicine_name": m.medicine_name,
        "generic_name": m.generic_name,
        "medicine_type": m.medicine_type,
        "category": m.category,
        "manufacturer": m.manufacturer,
        "batch_number": m.batch_number,
        "dosage": m.dosage,
        "unit": m.unit,
        "quantity": m.quantity,
        "reorder_level": m.reorder_level,
        "purchase_price": float(m.purchase_price),
        "selling_price": float(m.selling_price),
        "manufacture_date": str(m.manufacture_date) if m.manufacture_date else "",
        "expiry_date": str(m.expiry_date) if m.expiry_date else "",
        "storage_location": m.storage_location,
        "prescription_required": m.prescription_required,
        "status": m.status,
    }


@router.get("")
def get_medicines(db: Session = Depends(get_db)):
    medicines = db.query(Medicine).order_by(Medicine.medicine_name.asc()).all()
    return [_format_medicine(m) for m in medicines]


@router.get("/{medicine_id}")
def get_medicine(medicine_id: int, db: Session = Depends(get_db)):
    med = db.query(Medicine).filter(Medicine.id == medicine_id).first()
    if not med:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medicine not found"
        )
    return _format_medicine(med)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_medicine(data: MedicineCreate, db: Session = Depends(get_db)):
    existing = db.query(Medicine).filter(Medicine.medicine_code == data.medicine_code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Medicine code already exists"
        )

    status_val = data.status
    if data.quantity <= 0:
        status_val = "Out of Stock"
    elif data.quantity <= data.reorder_level:
        status_val = "Low Stock"
    else:
        status_val = "Available"

    med = Medicine(**data.model_dump())
    med.status = status_val
    db.add(med)
    db.commit()
    db.refresh(med)
    return _format_medicine(med)


@router.put("/{medicine_id}")
def update_medicine(medicine_id: int, data: MedicineUpdate, db: Session = Depends(get_db)):
    med = db.query(Medicine).filter(Medicine.id == medicine_id).first()
    if not med:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medicine not found"
        )

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(med, field, value)

    if med.quantity <= 0:
        med.status = "Out of Stock"
    elif med.quantity <= med.reorder_level:
        med.status = "Low Stock"
    else:
        med.status = "Available"

    db.commit()
    db.refresh(med)
    return _format_medicine(med)


@router.delete("/{medicine_id}")
def delete_medicine(medicine_id: int, db: Session = Depends(get_db)):
    med = db.query(Medicine).filter(Medicine.id == medicine_id).first()
    if not med:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medicine not found"
        )

    db.delete(med)
    db.commit()
    return {"message": "Medicine deleted successfully"}
