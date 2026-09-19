from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.attendance import Attendance
from app.models.staff import Staff
from app.schemas.attendance import AttendanceCreate, AttendanceResponse, AttendanceUpdate

router = APIRouter(
    prefix="/api/attendance",
    tags=["Attendance"]
)


def _format_attendance(a: Attendance) -> dict:
    return {
        "id": a.id,
        "staff_id": a.staff_id,
        "employee_id": a.employee_id or f"EMP-{1000 + (a.staff_id or a.id)}",
        "name": a.staff_name,
        "staff_name": a.staff_name,
        "role": a.role,
        "department": a.department,
        "date": str(a.date),
        "shift": a.shift or "09:00 AM - 05:00 PM",
        "check_in": a.check_in,
        "check_out": a.check_out,
        "status": a.status,
    }


@router.get("")
def get_attendance(target_date: Optional[date] = None, db: Session = Depends(get_db)):
    query = db.query(Attendance)
    if target_date:
        query = query.filter(Attendance.date == target_date)
    records = query.order_by(Attendance.date.desc(), Attendance.id.asc()).all()
    return [_format_attendance(r) for r in records]


@router.post("", status_code=status.HTTP_201_CREATED)
def mark_attendance(data: AttendanceCreate, db: Session = Depends(get_db)):
    # Check if existing record exists for this staff on this date
    existing = None
    if data.staff_id:
        existing = db.query(Attendance).filter(
            Attendance.staff_id == data.staff_id,
            Attendance.date == data.date
        ).first()

    if existing:
        existing.status = data.status
        if data.check_in:
            existing.check_in = data.check_in
        if data.check_out:
            existing.check_out = data.check_out
        if data.shift:
            existing.shift = data.shift
        db.commit()
        db.refresh(existing)
        return _format_attendance(existing)

    staff_name = data.staff_name
    role = data.role
    dept = data.department
    emp_id = data.employee_id

    if data.staff_id:
        staff = db.query(Staff).filter(Staff.id == data.staff_id).first()
        if staff:
            staff_name = staff.name
            role = staff.role
            dept = getattr(staff, "department", role)
            emp_id = emp_id or f"EMP-{1000 + staff.id}"

    rec = Attendance(
        staff_id=data.staff_id,
        employee_id=emp_id,
        staff_name=staff_name,
        role=role,
        department=dept,
        date=data.date,
        shift=data.shift,
        check_in=data.check_in,
        check_out=data.check_out,
        status=data.status,
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return _format_attendance(rec)


@router.put("/{attendance_id}")
def update_attendance(attendance_id: int, data: AttendanceUpdate, db: Session = Depends(get_db)):
    rec = db.query(Attendance).filter(Attendance.id == attendance_id).first()
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance record not found"
        )

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(rec, field, value)

    db.commit()
    db.refresh(rec)
    return _format_attendance(rec)
