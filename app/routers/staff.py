from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.staff import Staff
from app.models.user import User
from app.schemas.staff import StaffCreate, StaffResponse, StaffUpdate
from app.core.dependencies import require_role, require_admin


router = APIRouter(
    prefix="/api/staff",
    tags=["Staff"]
)


@router.get(
    "",
    response_model=list[StaffResponse]
)
def get_staff(
    db: Session = Depends(get_db)
):
    staff = (
        db.query(Staff)
        .order_by(Staff.id.desc())
        .all()
    )

    return staff


@router.get(
    "/{staff_id}",
    response_model=StaffResponse
)
def get_staff_member(
    staff_id: int,
    db: Session = Depends(get_db)
):
    staff = (
        db.query(Staff)
        .filter(Staff.id == staff_id)
        .first()
    )

    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Staff member not found"
        )

    return staff


@router.post(
    "",
    response_model=StaffResponse,
    status_code=status.HTTP_201_CREATED
)
def create_staff(
    staff_data: StaffCreate,
    db: Session = Depends(get_db)
):
    new_staff = Staff(
        name=staff_data.name,
        role=staff_data.role,
        gender=staff_data.gender or "Male",
        date_of_birth=staff_data.date_of_birth,
        phone=staff_data.phone,
        email=staff_data.email,
        address=staff_data.address,
        qualification=staff_data.qualification,
        experience=staff_data.experience,
        joining_date=staff_data.joining_date,
        status=staff_data.status
    )

    db.add(new_staff)
    db.commit()
    db.refresh(new_staff)

    return new_staff


@router.put(
    "/{staff_id}",
    response_model=StaffResponse
)
def update_staff(
    staff_id: int,
    staff_data: StaffUpdate,
    db: Session = Depends(get_db)
):
    staff = (
        db.query(Staff)
        .filter(Staff.id == staff_id)
        .first()
    )

    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Staff member not found"
        )

    for field, value in staff_data.model_dump(exclude_unset=True).items():
        setattr(staff, field, value)

    db.commit()
    db.refresh(staff)

    return staff


@router.delete(
    "/{staff_id}"
)
def delete_staff(
    staff_id: int,
    db: Session = Depends(get_db)
):
    staff = (
        db.query(Staff)
        .filter(Staff.id == staff_id)
        .first()
    )

    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Staff member not found"
        )

    db.delete(staff)
    db.commit()

    return {
        "message": "Staff member deleted successfully"
    }