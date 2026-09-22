"""
Migration script to add persistent notification & recurrence tracking columns to follow_ups table.
Idempotent and safe: checks existing columns before altering table.
"""

from sqlalchemy import inspect, text
from app.database import engine, SessionLocal
from app.models.notification import Notification
from app.models.followup import FollowUp


def run_migration():
    print("=" * 60)
    print("RUNNING FOLLOW_UPS REMINDER MIGRATION")
    print("=" * 60)

    insp = inspect(engine)
    existing_cols = [col["name"] for col in insp.get_columns("follow_ups")]
    print("Existing columns in follow_ups:", existing_cols)

    columns_to_add = [
        ("notification_sent", "TINYINT(1) NOT NULL DEFAULT 0"),
        ("triggered_at", "DATETIME NULL"),
        ("last_notification_date", "DATE NULL"),
        ("is_recurring", "TINYINT(1) NOT NULL DEFAULT 0"),
        ("recurrence_interval", "VARCHAR(50) NULL"),
        ("recurrence_end_date", "DATE NULL"),
    ]

    with engine.begin() as conn:
        for col_name, col_type in columns_to_add:
            if col_name not in existing_cols:
                print(f"Adding column `{col_name}` ({col_type}) to `follow_ups`...")
                conn.execute(text(f"ALTER TABLE `follow_ups` ADD COLUMN `{col_name}` {col_type};"))
                print(f"[OK] Added `{col_name}`.")
            else:
                print(f"[SKIP] `{col_name}` already exists.")

    # Backfill existing follow-ups that already generated notifications so duplicates are avoided
    db = SessionLocal()
    try:
        followups = db.query(FollowUp).all()
        for fu in followups:
            ref_code = fu.follow_up_code or f"FU-{fu.id}"
            notif = (
                db.query(Notification)
                .filter(
                    (Notification.related_entity_type == "followup") & (Notification.related_entity_id == fu.id)
                    | (Notification.type == "Follow-up") & (Notification.message.like(f"%{ref_code}%"))
                )
                .first()
            )
            if notif and not fu.notification_sent:
                fu.notification_sent = True
                fu.last_notification_date = fu.follow_up_date
                fu.triggered_at = notif.created_at
        db.commit()
        print("[OK] Backfilled legacy follow-up notification states.")
    except Exception as e:
        print("[NOTE] Migration backfill note:", e)
        db.rollback()
    finally:
        db.close()

    print("=" * 60)
    print("FOLLOW_UPS REMINDER MIGRATION COMPLETED SUCCESSFULLY")
    print("=" * 60)


if __name__ == "__main__":
    run_migration()
