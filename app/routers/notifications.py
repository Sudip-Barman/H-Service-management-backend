from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.notification import Notification
from app.models.user import User
from app.core.dependencies import get_current_user
from app.schemas.notification import (
    NotificationCreate,
    NotificationResponse,
    NotificationUpdate,
)

router = APIRouter(
    prefix="/api/notifications",
    tags=["Notifications"]
)


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
        "recipient_user_id": n.recipient_user_id,
        "recipient_role": n.recipient_role,
        "related_entity_type": n.related_entity_type,
        "related_entity_id": n.related_entity_id,
        "action_url": n.action_url,
    }


@router.get("")
def get_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns notifications strictly belonging to the currently authenticated user.
    Admin receives Admin-targeted and system notifications.
    Doctors, Nurses, and Staff only receive notifications matching their user ID.
    No automatic database mutations on GET.
    """
    if current_user.role == "admin":
        notifications = (
            db.query(Notification)
            .filter(
                (Notification.recipient_user_id == current_user.id)
                | (Notification.recipient_role == "admin")
                | (Notification.recipient_user_id == None)
            )
            .order_by(Notification.id.desc())
            .all()
        )
    else:
        notifications = (
            db.query(Notification)
            .filter(Notification.recipient_user_id == current_user.id)
            .order_by(Notification.id.desc())
            .all()
        )

    return [_format_notification(n) for n in notifications]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_notification(
    data: NotificationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notif = Notification(**data.model_dump())
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return _format_notification(notif)


@router.put("/mark-all-read")
@router.post("/mark-all-read")
def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Marks all notifications as read strictly scoped to the authenticated user.
    """
    if current_user.role == "admin":
        db.query(Notification).filter(
            Notification.read == False,
            (
                (Notification.recipient_user_id == current_user.id)
                | (Notification.recipient_role == "admin")
                | (Notification.recipient_user_id == None)
            )
        ).update({"read": True}, synchronize_session=False)
    else:
        db.query(Notification).filter(
            Notification.read == False,
            Notification.recipient_user_id == current_user.id
        ).update({"read": True}, synchronize_session=False)

    db.commit()
    return {"message": "All notifications marked as read"}


@router.put("/{notification_id}")
def update_notification(
    notification_id: int,
    data: NotificationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )

    if current_user.role != "admin" and notif.recipient_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update this notification"
        )

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(notif, field, value)

    db.commit()
    db.refresh(notif)
    return _format_notification(notif)


@router.put("/{notification_id}/read")
def mark_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )

    if current_user.role != "admin" and notif.recipient_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to mark this notification as read"
        )

    notif.read = True
    db.commit()
    return {"message": "Notification marked as read"}


@router.delete("/{notification_id}")
def delete_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )

    if current_user.role != "admin" and notif.recipient_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this notification"
        )

    db.delete(notif)
    db.commit()
    return {"message": "Notification deleted successfully"}
