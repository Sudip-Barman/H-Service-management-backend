from datetime import date as dt_date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.doctor import Doctor
from app.models.nurse import Nurse
from app.models.schedule import Schedule
from app.models.staff import Staff
from app.models.user import User
from app.schemas.schedule import ScheduleCreate, ScheduleResponse, ScheduleUpdate
from app.services.notification_service import create_targeted_notification

router = APIRouter(
    prefix="/api/schedules",
    tags=["Schedules"]
)


def _format_schedule(s: Schedule) -> dict:
    return {
        "id": s.id,
        "schedule_id": s.id,
        "doctor_id": s.doctor_id,
        "doctor_name": s.doctor_name,
        "department": s.department,
        "date": str(s.date),
        "start_date": str(s.start_date or s.date),
        "end_date": str(s.end_date or s.date),
        "start_time": s.start_time,
        "end_time": s.end_time,
        "location": s.location,
        "type": s.type,
        "status": s.status,
    }


def _notify_schedule(schedule: Schedule, action: str, db: Session):
    if not schedule.doctor_id and not schedule.doctor_name:
        return

    recipient_user_id = None
    recipient_role = "doctor"
    recipient_name = schedule.doctor_name or "Staff Member"

    # 1. Try finding Doctor
    if schedule.doctor_id:
        doc = db.query(Doctor).filter(Doctor.id == schedule.doctor_id).first()
        if doc and doc.user_id:
            recipient_user_id = doc.user_id
            recipient_role = "doctor"
            recipient_name = f"Dr. {doc.first_name} {doc.last_name or ''}".strip()

    # 2. Try finding Nurse
    if not recipient_user_id and schedule.doctor_id:
        nurse = db.query(Nurse).filter(Nurse.id == schedule.doctor_id).first()
        if nurse and nurse.user_id:
            recipient_user_id = nurse.user_id
            recipient_role = "nurse"
            recipient_name = f"Nurse {nurse.first_name} {nurse.last_name or ''}".strip()

    # 3. Try finding Staff
    if not recipient_user_id and schedule.doctor_id:
        st = db.query(Staff).filter(Staff.id == schedule.doctor_id).first()
        if st and st.user_id:
            recipient_user_id = st.user_id
            recipient_role = (st.role or "staff").lower()
            recipient_name = st.name

    # 4. Fallback lookup by name in User
    if not recipient_user_id and schedule.doctor_name:
        clean_name = schedule.doctor_name.replace("Dr.", "").replace("Nurse", "").strip()
        user_match = db.query(User).filter(
            (User.name.ilike(f"%{clean_name}%")) | (User.username.ilike(f"%{clean_name}%"))
        ).first()
        if user_match:
            recipient_user_id = user_match.id
            recipient_role = user_match.role
            recipient_name = user_match.name

    if not recipient_user_id:
        return

    title = "New Schedule Assigned" if action == "create" else "Schedule Updated"
    msg = f"Your schedule for {schedule.date} ({schedule.start_time} - {schedule.end_time}) at {schedule.location or 'Hospital'} has been {action}d."
    create_targeted_notification(
        db=db,
        title=title,
        message=msg,
        recipient_user_id=recipient_user_id,
        recipient_role=recipient_role,
        notif_type="schedule_changed",
        priority="Normal",
        department=schedule.department or "Clinical",
        recipient=recipient_name,
        related_entity_type="schedule",
        related_entity_id=schedule.id,
        action_url="/workforce/schedule",
    )


@router.get("")
def get_schedules(db: Session = Depends(get_db)):
    schedules = db.query(Schedule).order_by(Schedule.date.asc(), Schedule.start_time.asc()).all()
    return [_format_schedule(s) for s in schedules]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_schedule(data: ScheduleCreate, db: Session = Depends(get_db)):
    department = data.department
    doctor_name = data.doctor_name

    if data.doctor_id:
        doc = db.query(Doctor).filter(Doctor.id == data.doctor_id).first()
        if doc:
            doctor_name = f"Dr. {doc.first_name} {doc.last_name or ''}".strip()
            department = doc.department
        else:
            staff = db.query(Staff).filter(Staff.id == data.doctor_id).first()
            if staff:
                doctor_name = staff.name
                department = getattr(staff, "department", department)

    sched_date = data.start_date or data.date or dt_date.today()

    schedule = Schedule(
        doctor_id=data.doctor_id,
        doctor_name=doctor_name,
        department=department,
        date=sched_date,
        start_date=data.start_date or sched_date,
        end_date=data.end_date or sched_date,
        start_time=data.start_time,
        end_time=data.end_time,
        location=data.location,
        type=data.type,
        status=data.status
    )
    db.add(schedule)
    db.flush()

    _notify_schedule(schedule, "create", db)

    db.commit()
    db.refresh(schedule)
    return _format_schedule(schedule)


@router.put("/{schedule_id}")
def update_schedule(schedule_id: int, data: ScheduleUpdate, db: Session = Depends(get_db)):
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )

    update_data = data.model_dump(exclude_unset=True)
    if "doctor_id" in update_data and update_data["doctor_id"]:
        doc = db.query(Doctor).filter(Doctor.id == update_data["doctor_id"]).first()
        if doc:
            update_data["doctor_name"] = f"Dr. {doc.first_name} {doc.last_name or ''}".strip()
            update_data["department"] = doc.department
        else:
            staff = db.query(Staff).filter(Staff.id == update_data["doctor_id"]).first()
            if staff:
                update_data["doctor_name"] = staff.name
                if hasattr(staff, "department") and staff.department:
                    update_data["department"] = staff.department

    for field, value in update_data.items():
        setattr(schedule, field, value)

    _notify_schedule(schedule, "update", db)

    db.commit()
    db.refresh(schedule)
    return _format_schedule(schedule)


@router.delete("/{schedule_id}")
def delete_schedule(schedule_id: int, db: Session = Depends(get_db)):
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )

    db.delete(schedule)
    db.commit()
    return {"message": "Schedule deleted successfully"}
