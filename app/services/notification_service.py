from datetime import date, datetime
from sqlalchemy.orm import Session

from app.models.followup import FollowUp
from app.models.notification import Notification


def create_system_notification(
    db: Session,
    title: str,
    message: str,
    notif_type: str = "General",
    priority: str = "Normal",
    department: str = "General",
    recipient: str = "All Hospital Staff",
) -> Notification:
    """
    Creates and records a system notification in the database.
    """
    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    now_time = datetime.utcnow().strftime("%H:%M")

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
    )
    db.add(notif)
    # The caller will commit or commit here if caller handles commit
    return notif


def sync_followup_reminders(db: Session) -> int:
    """
    Checks for any pending/active follow-ups whose follow_up_date is today or earlier,
    and creates a reminder notification if one has not already been created for today.
    Returns the number of new reminder notifications generated.
    """
    today = date.today()
    today_str = today.strftime("%Y-%m-%d")

    # Exclude completed, cancelled, or closed follow-ups
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
        # Check if a reminder for this follow-up already exists for today
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
            
            notif = Notification(
                title=f"Follow-Up Reminder: {fu.name}",
                message=f"Follow-up {ref_code} for patient {fu.name} is scheduled {due_label}. Purpose: {fu.query or fu.followup_type or 'Check-up'}. Assigned to: {fu.assigned_to or 'Reception'}.",
                type="Follow-up",
                priority=priority_val,
                department="Reception",
                recipient=fu.assigned_to or "All Reception Staff",
                date=today_str,
                time=datetime.utcnow().strftime("%H:%M"),
                read=False,
            )
            db.add(notif)
            created_count += 1

    if created_count > 0:
        db.commit()

    return created_count
