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
        "createdAt": str(f.created_at.date()) if f.created_at else "",
    }


@router.get("")
def get_followups(db: Session = Depends(get_db)):
    items = db.query(FollowUp).order_by(FollowUp.id.desc()).all()
    return [_format_followup(f) for f in items]


from datetime import date
from app.services.notification_service import create_system_notification


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
    )
    db.add(fu)

    # Automated Notification Trigger
    today = date.today()
    ref_code = fu.follow_up_code or "FU"
    if fu.follow_up_date and fu.follow_up_date <= today:
        create_system_notification(
            db=db,
            title=f"Follow-Up Reminder: {fu.name}",
            message=f"Follow-up {ref_code} for patient {fu.name} is scheduled for today ({fu.follow_up_date}). Purpose: {fu.query or fu.followup_type or 'Check-up'}. Assigned to: {fu.assigned_to or 'Reception'}.",
            notif_type="Follow-up",
            priority="Urgent" if fu.priority in ["High", "Urgent"] else "Normal",
            department="Reception",
            recipient=fu.assigned_to or "All Reception Staff",
        )
    else:
        create_system_notification(
            db=db,
            title=f"New Follow-Up Scheduled: {fu.name}",
            message=f"Follow-up {ref_code} scheduled for {fu.name} on {fu.follow_up_date}. Purpose: {fu.query or fu.followup_type or 'Check-up'}. Assigned to: {fu.assigned_to or 'Reception'}.",
            notif_type="Follow-up",
            priority="Normal",
            department="Reception",
            recipient=fu.assigned_to or "All Reception Staff",
        )

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

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(fu, field, value)

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
