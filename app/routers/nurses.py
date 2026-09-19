from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.nurse import Nurse
from app.schemas.nurse import NurseCreate, NurseResponse, NurseUpdate

router = APIRouter(
    prefix="/api/nurses",
    tags=["Nurses"]
)


@router.get("", response_model=list[NurseResponse])
def get_nurses(db: Session = Depends(get_db)):
    return db.query(Nurse).order_by(Nurse.id.desc()).all()


@router.get("/{nurse_id}", response_model=NurseResponse)
def get_nurse(nurse_id: int, db: Session = Depends(get_db)):
    nurse = db.query(Nurse).filter(Nurse.id == nurse_id).first()
    if not nurse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nurse not found"
        )
    return nurse


@router.post("", response_model=NurseResponse, status_code=status.HTTP_201_CREATED)
def create_nurse(data: NurseCreate, db: Session = Depends(get_db)):
    existing = db.query(Nurse).filter(
        Nurse.registration_number == data.registration_number
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nurse with this registration number already exists"
        )

    nurse = Nurse(**data.model_dump())
    db.add(nurse)
    db.commit()
    db.refresh(nurse)
    return nurse


@router.put("/{nurse_id}", response_model=NurseResponse)
def update_nurse(nurse_id: int, data: NurseUpdate, db: Session = Depends(get_db)):
    nurse = db.query(Nurse).filter(Nurse.id == nurse_id).first()
    if not nurse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nurse not found"
        )

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(nurse, field, value)

    db.commit()
    db.refresh(nurse)
    return nurse


@router.delete("/{nurse_id}", status_code=status.HTTP_200_OK)
def delete_nurse(nurse_id: int, db: Session = Depends(get_db)):
    nurse = db.query(Nurse).filter(Nurse.id == nurse_id).first()
    if not nurse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nurse not found"
        )

    db.delete(nurse)
    db.commit()
    return {"message": "Nurse deleted successfully"}
