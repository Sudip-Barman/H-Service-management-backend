import calendar
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session

from app.models.followup import FollowUp
from app.models.notification import Notification
from app.models.reminder_log import ReminderNotificationLog
from app.models.user import User
from app.utils.datetime_utils import get_current_ist_date


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


def add_calendar_months(orig_date: date, months: int = 1) -> date:
    """
    Safely adds calendar months to a date, clamping day to end of month
    (e.g., Jan 31 + 1 month -> Feb 28 or 29).
    """
    year = orig_date.year + (orig_date.month + months - 1) // 12
    month = (orig_date.month + months - 1) % 12 + 1
    max_day = calendar.monthrange(year, month)[1]
    day = min(orig_date.day, max_day)
    return date(year, month, day)


def advance_recurring_followup(fu: FollowUp, base_date: date | None = None) -> date | None:
    """
    Advances a recurring follow-up to its next scheduled occurrence date.
    Returns the next date, or None if recurrence has expired.
    Uses calendar-month logic for monthly recurrence.
    """
    if not fu.is_recurring:
        return None

    today = get_current_ist_date()
    interval = (fu.recurrence_interval or "Daily").strip().capitalize()
    ref = base_date or fu.follow_up_date or today
    if ref < today:
        ref = today

    if interval == "Daily":
        next_date = ref + timedelta(days=1)
    elif interval == "Weekly":
        next_date = ref + timedelta(weeks=1)
    elif interval == "Monthly":
        next_date = add_calendar_months(ref, 1)
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
    and creates a reminder notification if one has not already been created for that occurrence.
    Uses persistent database tracking in ReminderNotificationLog (reminder_type, reminder_id, occurrence_date, recipient_key).
    Deleting or dismissing a notification will NEVER cause that occurrence to be regenerated.
    """
    today = get_current_ist_date()
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
        scheduled_date_str = str(fu.follow_up_date)

        # Check persistent ReminderNotificationLog: if this exact occurrence was already notified, NEVER re-notify!
        already_logged = (
            db.query(ReminderNotificationLog)
            .filter(
                ReminderNotificationLog.reminder_type == "followup",
                ReminderNotificationLog.reminder_id == fu.id,
                ReminderNotificationLog.occurrence_date == scheduled_date_str,
                ReminderNotificationLog.recipient_key == "admin",
            )
            .first()
        )
        if already_logged:
            fu.notification_sent = True
            fu.last_notification_date = fu.follow_up_date
            if fu.is_recurring and fu.follow_up_date <= today:
                advance_recurring_followup(fu, base_date=fu.follow_up_date)
            continue

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

        # Record in persistent ReminderNotificationLog so deleting the notification never recreates it
        log_entry = ReminderNotificationLog(
            reminder_type="followup",
            reminder_id=fu.id,
            occurrence_date=scheduled_date_str,
            recipient_key="admin",
            created_at=now,
        )
        db.add(log_entry)

        # Mark persistently as triggered for this scheduled occurrence
        fu.notification_sent = True
        fu.last_notification_date = scheduled_date_for_this_occurrence
        fu.triggered_at = now

        # If recurring, advance to next occurrence date (treated as separate future occurrence)
        if fu.is_recurring:
            advance_recurring_followup(fu, base_date=scheduled_date_for_this_occurrence)

        created_count += 1

    if created_count > 0:
        db.commit()

    return created_count


