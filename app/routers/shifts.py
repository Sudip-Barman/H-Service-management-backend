from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.shift import StaffShift
from app.models.staff import Staff
from app.schemas.shift import ShiftCreate, ShiftResponse, ShiftUpdate

router = APIRouter(
    prefix="/api/shifts",
    tags=["Shifts"]
)


def _format_shift(s: StaffShift) -> dict:
    return {
        "id": s.id,
        "shift_id": s.id,
        "shift_code": s.shift_code or f"SH-{1000 + s.id}",
        "staff": s.staff_name,
        "staff_name": s.staff_name,
        "staff_id": s.staff_id,
        "employeeId": s.employee_id or f"EMP-{1000 + (s.staff_id or s.id)}",
        "employee_id": s.employee_id,
        "department": s.department,
        "date": str(s.date),
        "shift": s.shift,
        "startTime": s.start_time,
        "start_time": s.start_time,
        "endTime": s.end_time,
        "end_time": s.end_time,
        "location": s.location,
        "status": s.status,
        "notes": s.notes,
    }


@router.get("")
def get_shifts(db: Session = Depends(get_db)):
    shifts = db.query(StaffShift).order_by(StaffShift.date.desc(), StaffShift.start_time.asc()).all()
    return [_format_shift(s) for s in shifts]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_shift(data: ShiftCreate, db: Session = Depends(get_db)):
    staff_name = data.staff_name
    department = data.department
    employee_id = data.employee_id

    # If staff_id is supplied, auto-sync staff details
    if data.staff_id:
        staff = db.query(Staff).filter(Staff.id == data.staff_id).first()
        if staff:
            staff_name = staff.name
            department = getattr(staff, "department", None) or getattr(staff, "role", department)
            employee_id = employee_id or f"EMP-{1000 + staff.id}"

    shift = StaffShift(
        shift_code=data.shift_code,
        staff_id=data.staff_id,
        staff_name=staff_name,
        employee_id=employee_id,
        department=department,
        date=data.date,
        shift=data.shift,
        start_time=data.start_time,
        end_time=data.end_time,
        location=data.location,
        status=data.status,
        notes=data.notes,
    )
    db.add(shift)
    db.commit()
    db.refresh(shift)
    return _format_shift(shift)


@router.put("/{shift_id}")
def update_shift(shift_id: int, data: ShiftUpdate, db: Session = Depends(get_db)):
    shift = db.query(StaffShift).filter(StaffShift.id == shift_id).first()
    if not shift:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shift not found"
        )

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(shift, field, value)

    db.commit()
    db.refresh(shift)
    return _format_shift(shift)


@router.delete("/{shift_id}")
def delete_shift(shift_id: int, db: Session = Depends(get_db)):
    shift = db.query(StaffShift).filter(StaffShift.id == shift_id).first()
    if not shift:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shift not found"
        )

    db.delete(shift)
    db.commit()
    return {"message": "Shift deleted successfully"}
