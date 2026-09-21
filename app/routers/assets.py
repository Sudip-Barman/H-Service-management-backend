from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.asset import HospitalAsset
from app.schemas.asset import AssetCreate, AssetResponse, AssetUpdate

router = APIRouter(
    prefix="/api/assets",
    tags=["Assets"]
)


def _format_asset(a: HospitalAsset) -> dict:
    return {
        "id": a.id,
        "asset_code": a.asset_code,
        "name": a.name,
        "category": a.category,
        "department": a.department,
        "model_number": a.model_number or "",
        "serial_number": a.serial_number or "",
        "location": a.location or "",
        "purchase_cost": float(a.purchase_cost) if a.purchase_cost is not None else 0.0,
        "purchase_date": str(a.purchase_date) if a.purchase_date else "",
        "warranty_expiry": str(a.warranty_expiry) if a.warranty_expiry else "",
        "next_maintenance": str(a.next_maintenance) if a.next_maintenance else "",
        "assigned_to": a.assigned_to or "",
        "condition": a.condition or "Good",
        "status": a.status or "Operational",
        "notes": a.notes or "",
        "created_at": a.created_at.isoformat() if a.created_at else "",
        "updated_at": a.updated_at.isoformat() if a.updated_at else "",
    }


@router.get("")
def get_assets(db: Session = Depends(get_db)):
    assets = db.query(HospitalAsset).order_by(HospitalAsset.id.desc()).all()
    return [_format_asset(a) for a in assets]


@router.get("/{asset_id}")
def get_asset(asset_id: int, db: Session = Depends(get_db)):
    asset = db.query(HospitalAsset).filter(HospitalAsset.id == asset_id).first()
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )
    return _format_asset(asset)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_asset(data: AssetCreate, db: Session = Depends(get_db)):
    existing = db.query(HospitalAsset).filter(HospitalAsset.asset_code == data.asset_code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Asset with code '{data.asset_code}' already exists"
        )

    asset = HospitalAsset(**data.model_dump())
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return _format_asset(asset)


@router.put("/{asset_id}")
def update_asset(asset_id: int, data: AssetUpdate, db: Session = Depends(get_db)):
    asset = db.query(HospitalAsset).filter(HospitalAsset.id == asset_id).first()
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(asset, key, value)

    db.commit()
    db.refresh(asset)
    return _format_asset(asset)


@router.delete("/{asset_id}")
def delete_asset(asset_id: int, db: Session = Depends(get_db)):
    asset = db.query(HospitalAsset).filter(HospitalAsset.id == asset_id).first()
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )

    db.delete(asset)
    db.commit()
    return {"message": "Asset deleted successfully", "id": asset_id}
