from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.notification import Notification
from app.schemas.notification import (
    NotificationCreate,
    NotificationResponse,
    NotificationUpdate,
)

router = APIRouter(
    prefix="/api/notifications",
    tags=["Notifications"]
)


from app.services.notification_service import sync_followup_reminders


def _format_notification(n: Notification) -> dict:
    return {
        "id": n.id,
        "title": n.title,
        "message": n.message,
        "type": n.type,
        "priority": n.priority,
        "department": n.department or "General",
        "recipient": n.recipient or "All Clinical Staff",
        "date": n.date or str(n.created_at.date()),
        "time": n.time or n.created_at.strftime("%H:%M"),
        "read": n.read,
    }


@router.get("")
def get_notifications(db: Session = Depends(get_db)):
    try:
        sync_followup_reminders(db)
    except Exception as e:
        # Prevent any potential follow-up sync issue from breaking notification retrieval
        pass

    notifications = db.query(Notification).order_by(Notification.id.desc()).all()
    return [_format_notification(n) for n in notifications]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_notification(data: NotificationCreate, db: Session = Depends(get_db)):
    notif = Notification(**data.model_dump())
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return _format_notification(notif)


@router.put("/mark-all-read")
@router.post("/mark-all-read")
def mark_all_read(db: Session = Depends(get_db)):
    db.query(Notification).filter(Notification.read == False).update({"read": True})
    db.commit()
    return {"message": "All notifications marked as read"}


@router.put("/{notification_id}")
def update_notification(notification_id: int, data: NotificationUpdate, db: Session = Depends(get_db)):
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(notif, field, value)

    db.commit()
    db.refresh(notif)
    return _format_notification(notif)


@router.put("/{notification_id}/read")
def mark_read(notification_id: int, db: Session = Depends(get_db)):
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )

    notif.read = True
    db.commit()
    return {"message": "Notification marked as read"}


@router.delete("/{notification_id}")
def delete_notification(notification_id: int, db: Session = Depends(get_db)):
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )

    db.delete(notif)
    db.commit()
    return {"message": "Notification deleted successfully"}
