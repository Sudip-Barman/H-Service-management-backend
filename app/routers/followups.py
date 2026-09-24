from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.followup import FollowUp
from app.models.patient import Patient
from app.schemas.followup import FollowUpCreate, FollowUpResponse, FollowUpUpdate

router = APIRouter(
    prefix="/api/follow-ups",
    tags=["Follow Ups"]
)


from datetime import date, datetime
from app.models.reminder_log import ReminderNotificationLog
from app.utils.datetime_utils import get_current_ist_date
from app.services.notification_service import (
    advance_recurring_followup,
    create_targeted_notification,
    sync_followup_reminders,
)


def _format_followup(f: FollowUp) -> dict:
    return {
        "id": f.follow_up_code or f"FU-{1000 + f.id}",
        "follow_up_id": f.id,
        "name": f.name,
        "phone": f.phone,
        "email": f.email or "",
        "patientId": f.patient_id or "",
        "patient_id": f.patient_id,
        "relation": f.relation or "Self",
        "source": f.source or "Phone Call",
        "type": f.followup_type,
        "query": f.query or "",
        "priority": f.priority,
        "followUpDate": str(f.follow_up_date),
        "follow_up_date": str(f.follow_up_date),
        "assignedTo": f.assigned_to or "Reception",
        "assigned_to": f.assigned_to or "Reception",
        "notes": f.notes or "",
        "nextAction": f.next_action or "",
        "status": f.status,
        "notification_sent": f.notification_sent,
        "triggered_at": f.triggered_at.isoformat() if f.triggered_at else None,
        "last_notification_date": str(f.last_notification_date) if f.last_notification_date else None,
        "is_recurring": f.is_recurring,
        "recurrence_interval": f.recurrence_interval,
        "recurrence_end_date": str(f.recurrence_end_date) if f.recurrence_end_date else None,
        "createdAt": str(f.created_at.date()) if f.created_at else "",
    }


@router.get("")
def get_followups(db: Session = Depends(get_db)):
    items = db.query(FollowUp).order_by(FollowUp.id.desc()).all()
    return [_format_followup(f) for f in items]


@router.post("/sync-reminders")
def sync_reminders(db: Session = Depends(get_db)):
    """
    Triggers check for due reminders and generates notifications exactly once.
    """
    count = sync_followup_reminders(db)
    return {"status": "success", "synced_count": count}


@router.post("", status_code=status.HTTP_201_CREATED)
def create_followup(data: FollowUpCreate, db: Session = Depends(get_db)):
    # Auto-fill patient details if patient_id is provided
    name = data.name
    phone = data.phone
    email = data.email
    if data.patient_id:
        p = db.query(Patient).filter(
            (Patient.registration_number == data.patient_id) |
            (Patient.id == (int(data.patient_id) if data.patient_id.isdigit() else 0))
        ).first()
        if p:
            name = f"{p.first_name} {p.last_name or ''}".strip()
            phone = p.phone or phone
            email = p.email or email

    fu = FollowUp(
        follow_up_code=data.follow_up_code,
        name=name,
        phone=phone,
        email=email,
        patient_id=data.patient_id,
        relation=data.relation,
        source=data.source,
        followup_type=data.followup_type,
        query=data.query,
        priority=data.priority,
        follow_up_date=data.follow_up_date,
        assigned_to=data.assigned_to,
        notes=data.notes,
        next_action=data.next_action,
        status=data.status,
        is_recurring=data.is_recurring,
        recurrence_interval=data.recurrence_interval,
        recurrence_end_date=data.recurrence_end_date,
        notification_sent=False,
    )
    db.add(fu)
    db.flush()

    # Automated Notification Trigger
    today = date.today()
    ref_code = fu.follow_up_code or "FU"
    if fu.follow_up_date and fu.follow_up_date <= today:
        priority_val = "Urgent" if fu.priority in ["High", "Urgent"] else "Normal"
        due_label = "today" if fu.follow_up_date == today else f"on {fu.follow_up_date} (Overdue)"
        scheduled_date_for_this_occurrence = fu.follow_up_date

        create_targeted_notification(
            db=db,
            title=f"Follow-Up Reminder: {fu.name}",
            message=f"Follow-up {ref_code} for patient {fu.name} is scheduled {due_label}. Purpose: {fu.query or fu.followup_type or 'Check-up'}. Assigned to: {fu.assigned_to or 'Reception'}.",
            recipient_role="admin",
            notif_type="Follow-up",
            priority=priority_val,
            department="Reception",
            recipient=fu.assigned_to or "Administration & Reception",
            related_entity_type="followup",
            related_entity_id=fu.id,
            action_url="/admin/follow-up",
        )

        # Record in persistent ReminderNotificationLog so deleting the notification never recreates it
        db.add(
            ReminderNotificationLog(
                reminder_type="followup",
                reminder_id=fu.id,
                occurrence_date=str(scheduled_date_for_this_occurrence),
                recipient_key="admin",
                created_at=datetime.utcnow(),
            )
        )

        fu.notification_sent = True
        fu.last_notification_date = scheduled_date_for_this_occurrence
        fu.triggered_at = datetime.utcnow()

        if fu.is_recurring:
            advance_recurring_followup(fu, base_date=scheduled_date_for_this_occurrence)
    else:
        create_targeted_notification(
            db=db,
            title=f"New Follow-Up Scheduled: {fu.name}",
            message=f"Follow-up {ref_code} scheduled for {fu.name} on {fu.follow_up_date}. Purpose: {fu.query or fu.followup_type or 'Check-up'}. Assigned to: {fu.assigned_to or 'Reception'}.",
            recipient_role="admin",
            notif_type="Follow-up",
            priority="Normal",
            department="Reception",
            recipient=fu.assigned_to or "Administration & Reception",
            related_entity_type="followup",
            related_entity_id=fu.id,
            action_url="/admin/follow-up",
        )
        fu.notification_sent = False
        fu.last_notification_date = None
        fu.triggered_at = None

    db.commit()
    db.refresh(fu)
    return _format_followup(fu)


@router.put("/{followup_id}")
def update_followup(followup_id: str, data: FollowUpUpdate, db: Session = Depends(get_db)):
    fu = db.query(FollowUp).filter(
        (FollowUp.follow_up_code == followup_id) | (FollowUp.id == (int(followup_id) if followup_id.isdigit() else 0))
    ).first()
    if not fu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Follow-up record not found"
        )

    prev_date = fu.follow_up_date
    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(fu, field, value)

    # If the user changed follow_up_date to a new date, handle notification_sent state
    if "follow_up_date" in update_data and update_data["follow_up_date"] != prev_date:
        new_date = update_data["follow_up_date"]
        if new_date > date.today():
            fu.notification_sent = False
            fu.triggered_at = None
        elif new_date <= date.today():
            if fu.last_notification_date != new_date:
                fu.notification_sent = False

    db.commit()
    db.refresh(fu)
    return _format_followup(fu)


@router.delete("/{followup_id}")
def delete_followup(followup_id: str, db: Session = Depends(get_db)):
    fu = db.query(FollowUp).filter(
        (FollowUp.follow_up_code == followup_id) | (FollowUp.id == (int(followup_id) if followup_id.isdigit() else 0))
    ).first()
    if not fu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Follow-up record not found"
        )

    db.delete(fu)
    db.commit()
    return {"message": "Follow-up deleted successfully"}

