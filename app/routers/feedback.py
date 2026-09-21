from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.feedback import Feedback
from app.schemas.feedback import FeedbackCreate, FeedbackResponse, FeedbackUpdate

router = APIRouter(
    prefix="/api/feedback",
    tags=["Feedback"]
)


def _format_feedback(fb: Feedback) -> dict:
    initials = "".join([part[0].upper() for part in fb.patient.strip().split()[:2]]) or "PT"
    return {
        "id": fb.feedback_code or f"FB-{2000 + fb.id}",
        "feedback_id": fb.id,
        "patient": fb.patient,
        "email": fb.email or "",
        "service": fb.service,
        "rating": fb.rating,
        "status": fb.status,
        "date": fb.date,
        "comment": fb.comment or "",
        "initials": initials,
    }


@router.get("")
def get_feedback(db: Session = Depends(get_db)):
    feedbacks = db.query(Feedback).order_by(Feedback.id.desc()).all()
    return [_format_feedback(f) for f in feedbacks]


from app.services.notification_service import create_system_notification


@router.post("", status_code=status.HTTP_201_CREATED)
def create_feedback(data: FeedbackCreate, db: Session = Depends(get_db)):
    code = data.feedback_code
    if not code:
        count = db.query(Feedback).count()
        code = f"FB-{2000 + count + 1}"

    fb = Feedback(
        feedback_code=code,
        patient=data.patient,
        email=data.email,
        service=data.service,
        rating=data.rating,
        status=data.status,
        date=data.date,
        comment=data.comment,
    )
    db.add(fb)

    # Automated Notification Trigger
    p_rating = fb.rating if fb.rating is not None else 5
    priority_level = "High" if p_rating <= 2 else "Normal"
    create_system_notification(
        db=db,
        title=f"New Patient Feedback: {fb.patient}",
        message=f"Feedback submitted by {fb.patient} for {fb.service} with {p_rating}★ rating: '{fb.comment or 'No additional comment'}'.",
        notif_type="Feedback",
        priority=priority_level,
        department="Patient Relations",
        recipient="Quality & Hospital Operations",
    )

    db.commit()
    db.refresh(fb)
    return _format_feedback(fb)


@router.put("/{feedback_id}")
def update_feedback(feedback_id: str, data: FeedbackUpdate, db: Session = Depends(get_db)):
    fb = db.query(Feedback).filter(
        (Feedback.feedback_code == feedback_id) | (Feedback.id == (int(feedback_id) if feedback_id.isdigit() else 0))
    ).first()
    if not fb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found"
        )

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(fb, field, value)

    db.commit()
    db.refresh(fb)
    return _format_feedback(fb)


@router.delete("/{feedback_id}")
def delete_feedback(feedback_id: str, db: Session = Depends(get_db)):
    fb = db.query(Feedback).filter(
        (Feedback.feedback_code == feedback_id) | (Feedback.id == (int(feedback_id) if feedback_id.isdigit() else 0))
    ).first()
    if not fb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found"
        )

    db.delete(fb)
    db.commit()
    return {"message": "Feedback deleted successfully"}
