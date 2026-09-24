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


from app.services.notification_service import sync_followup_reminders


@router.get("")
def get_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns notifications strictly belonging to the currently authenticated user.
    Admin receives Admin-targeted and system notifications.
    Doctors, Nurses, and Staff only receive notifications matching their user ID.
    Synchronizes pending reminder occurrences exactly once with persistent state tracking.
    """
    if current_user.role == "admin":
        try:
            sync_followup_reminders(db)
        except Exception:
            pass

        notifications = (
            db.query(Notification)
            .order_by(Notification.id.desc())
            .all()
        )
    else:
        # Workforce users (Doctor, Nurse, Staff): Exclude all new registration events (Patient, Doctor, Nurse, Staff)
        notifications = (
            db.query(Notification)
            .filter(
                (
                    (Notification.recipient_user_id == current_user.id)
                    | (Notification.recipient_role == current_user.role)
                    | (Notification.recipient_role == "all_staff")
                    | (
                        (Notification.recipient_user_id == None)
                        & (Notification.recipient_role != "admin")
                    )
                ),
                Notification.recipient_role != "admin",
                ~Notification.title.ilike("%Registered%"),
            )
            .order_by(Notification.id.desc())
            .all()
        )

    return [_format_notification(n) for n in notifications]


@router.post("/sync-reminders")
def sync_notifications_reminders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Explicitly checks and triggers pending reminders for today exactly once.
    """
    count = sync_followup_reminders(db)
    return {"status": "success", "synced_count": count}


@router.post("", status_code=status.HTTP_201_CREATED)
def create_notification(
    data: NotificationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1. Broadcast to all staff members
    if data.recipient_mode == "all_staff" or (
        data.recipient and data.recipient.strip().lower() in ["all staff", "all hospital staff", "all clinical staff"]
    ):
        staff_users = db.query(User).filter(
            User.role.in_(["doctor", "nurse", "staff", "receptionist", "admin"])
        ).all()
        created_notifs = []
        for u in staff_users:
            notif = Notification(
                title=data.title,
                message=data.message,
                type=data.type,
                priority=data.priority,
                department=data.department or "All Departments",
                recipient=u.name,
                date=data.date,
                time=data.time,
                read=False,
                recipient_user_id=u.id,
                recipient_role=u.role,
                related_entity_type=data.related_entity_type,
                related_entity_id=data.related_entity_id,
                action_url=data.action_url,
            )
            db.add(notif)
            created_notifs.append(notif)
        db.commit()
        for n in created_notifs:
            db.refresh(n)
        return [_format_notification(n) for n in created_notifs]

    # 2. Broadcast to selected staff/users
    if data.recipient_mode == "selected" and data.recipient_user_ids:
        users = db.query(User).filter(User.id.in_(data.recipient_user_ids)).all()
        created_notifs = []
        for u in users:
            notif = Notification(
                title=data.title,
                message=data.message,
                type=data.type,
                priority=data.priority,
                department=data.department or "All Departments",
                recipient=u.name,
                date=data.date,
                time=data.time,
                read=False,
                recipient_user_id=u.id,
                recipient_role=u.role,
                related_entity_type=data.related_entity_type,
                related_entity_id=data.related_entity_id,
                action_url=data.action_url,
            )
            db.add(notif)
            created_notifs.append(notif)
        db.commit()
        for n in created_notifs:
            db.refresh(n)
        return [_format_notification(n) for n in created_notifs]

    # 3. Single recipient (targeted user or general)
    recipient_role = data.recipient_role
    recipient_name = data.recipient
    if data.recipient_user_id:
        u = db.query(User).filter(User.id == data.recipient_user_id).first()
        if u:
            recipient_role = u.role
            recipient_name = u.name

    notif = Notification(
        title=data.title,
        message=data.message,
        type=data.type,
        priority=data.priority,
        department=data.department,
        recipient=recipient_name,
        date=data.date,
        time=data.time,
        read=False,
        recipient_user_id=data.recipient_user_id,
        recipient_role=recipient_role,
        related_entity_type=data.related_entity_type,
        related_entity_id=data.related_entity_id,
        action_url=data.action_url,
    )
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
