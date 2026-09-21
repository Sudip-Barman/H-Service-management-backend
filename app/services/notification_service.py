from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session

from app.models.followup import FollowUp
from app.models.notification import Notification
from app.models.user import User


def create_targeted_notification(
    db: Session,
    title: str,
    message: str,
    recipient_user_id: int | None = None,
    recipient_role: str | None = None,
    notif_type: str = "General",
    priority: str = "Normal",
    department: str = "General",
    recipient: str | None = None,
    related_entity_type: str | None = None,
    related_entity_id: int | None = None,
    action_url: str | None = None,
) -> Notification:
    """
    Creates a targeted notification specifically for a user or role.
    Prevents duplicate notifications for the same event generated within 60 seconds.
    """
    now = datetime.utcnow()
    today_str = now.strftime("%Y-%m-%d")
    now_time = now.strftime("%H:%M")

    # De-duplication check: if identical event notification was created recently, reuse it
    if related_entity_type and related_entity_id and (recipient_user_id or recipient_role):
        recent_cutoff = now - timedelta(seconds=60)
        query = db.query(Notification).filter(
            Notification.related_entity_type == related_entity_type,
            Notification.related_entity_id == related_entity_id,
            Notification.type == notif_type,
            Notification.created_at >= recent_cutoff,
        )
        if recipient_user_id:
            query = query.filter(Notification.recipient_user_id == recipient_user_id)
        elif recipient_role:
            query = query.filter(Notification.recipient_role == recipient_role)

        existing = query.first()
        if existing:
            return existing

    # Default recipient label if not provided
    if not recipient:
        if recipient_role:
            recipient = f"{recipient_role.capitalize()} Team"
        elif recipient_user_id:
            u = db.query(User).filter(User.id == recipient_user_id).first()
            recipient = u.name if u else f"User #{recipient_user_id}"
        else:
            recipient = "Hospital Staff"

    notif = Notification(
        title=title,
        message=message,
        type=notif_type,
        priority=priority,
        department=department,
        recipient=recipient,
        date=today_str,
        time=now_time,
        read=False,
        recipient_user_id=recipient_user_id,
        recipient_role=recipient_role,
        related_entity_type=related_entity_type,
        related_entity_id=related_entity_id,
        action_url=action_url,
        created_at=now,
    )
    db.add(notif)
    return notif


def create_system_notification(
    db: Session,
    title: str,
    message: str,
    notif_type: str = "General",
    priority: str = "Normal",
    department: str = "General",
    recipient: str = "Administration",
    recipient_user_id: int | None = None,
    recipient_role: str = "admin",
    related_entity_type: str | None = None,
    related_entity_id: int | None = None,
    action_url: str | None = None,
) -> Notification:
    """
    Creates and records a system/admin notification in the database.
    Defaults to Admin role to prevent broadcasting to clinical workforce.
    """
    return create_targeted_notification(
        db=db,
        title=title,
        message=message,
        recipient_user_id=recipient_user_id,
        recipient_role=recipient_role,
        notif_type=notif_type,
        priority=priority,
        department=department,
        recipient=recipient,
        related_entity_type=related_entity_type,
        related_entity_id=related_entity_id,
        action_url=action_url,
    )


def sync_followup_reminders(db: Session) -> int:
    """
    Checks for any pending/active follow-ups whose follow_up_date is today or earlier,
    and creates a reminder notification if one has not already been created for today.
    Targeted to Admin/Reception so workforce doctors/nurses don't see raw follow-up reminders.
    """
    today = date.today()
    today_str = today.strftime("%Y-%m-%d")

    active_followups = (
        db.query(FollowUp)
        .filter(
            FollowUp.follow_up_date <= today,
            ~FollowUp.status.in_(["Completed", "Cancelled", "Closed", "Done"]),
        )
        .all()
    )

    created_count = 0
    for fu in active_followups:
        ref_code = fu.follow_up_code or f"FU-{fu.id}"
        existing = (
            db.query(Notification)
            .filter(
                Notification.type == "Follow-up",
                Notification.date == today_str,
                Notification.message.like(f"%{ref_code}%"),
            )
            .first()
        )

        if not existing:
            priority_val = "Urgent" if fu.priority in ["High", "Urgent"] else "Normal"
            due_label = "today" if fu.follow_up_date == today else f"on {fu.follow_up_date} (Overdue)"

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
            created_count += 1

    if created_count > 0:
        db.commit()

    return created_count
