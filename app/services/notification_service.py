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


def advance_recurring_followup(fu: FollowUp, base_date: date | None = None) -> date | None:
    """
    Advances a recurring follow-up to its next scheduled occurrence date.
    Returns the next date, or None if recurrence has expired.
    """
    if not fu.is_recurring:
        return None

    interval = (fu.recurrence_interval or "Daily").strip().capitalize()
    ref = base_date or fu.follow_up_date or date.today()
    if ref < date.today():
        ref = date.today()

    if interval == "Daily":
        next_date = ref + timedelta(days=1)
    elif interval == "Weekly":
        next_date = ref + timedelta(weeks=1)
    elif interval == "Monthly":
        next_date = ref + timedelta(days=30)
    else:
        next_date = ref + timedelta(days=1)

    if fu.recurrence_end_date and next_date > fu.recurrence_end_date:
        fu.is_recurring = False
        return None

    fu.follow_up_date = next_date
    fu.notification_sent = False
    return next_date


def sync_followup_reminders(db: Session) -> int:
    """
    Checks for any pending/active follow-ups whose follow_up_date is today or earlier,
    and creates a reminder notification if one has not already been created for today.
    Uses persistent database tracking on FollowUp (notification_sent, last_notification_date, triggered_at).
    Deleting or dismissing a notification will NEVER recreate it.
    """
    today = date.today()
    now = datetime.utcnow()

    # Query only active follow-ups due today or earlier that have NOT yet been notified for their current scheduled date
    active_followups = (
        db.query(FollowUp)
        .filter(
            FollowUp.follow_up_date <= today,
            ~FollowUp.status.in_(["Completed", "Cancelled", "Closed", "Done"]),
            (
                (FollowUp.notification_sent == False)
                | (FollowUp.last_notification_date != FollowUp.follow_up_date)
                | (FollowUp.last_notification_date == None)
            ),
        )
        .all()
    )

    created_count = 0
    for fu in active_followups:
        # Extra safety check: if already triggered for this specific follow_up_date, skip
        if fu.notification_sent and fu.last_notification_date == fu.follow_up_date:
            continue

        ref_code = fu.follow_up_code or f"FU-{fu.id}"
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

        # Mark persistently as triggered for this scheduled occurrence
        fu.notification_sent = True
        fu.last_notification_date = scheduled_date_for_this_occurrence
        fu.triggered_at = now

        # If recurring, advance to next occurrence date
        if fu.is_recurring:
            advance_recurring_followup(fu, base_date=scheduled_date_for_this_occurrence)

        created_count += 1

    if created_count > 0:
        db.commit()

    return created_count

