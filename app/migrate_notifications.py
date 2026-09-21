"""
Migration script to add targeted notification columns to notifications table.
Idempotent and safe: checks columns before altering table.
"""

from sqlalchemy import inspect, text
from app.database import engine, SessionLocal
from app.models.user import User


def run_migration():
    print("=" * 60)
    print("RUNNING NOTIFICATIONS MIGRATION")
    print("=" * 60)

    insp = inspect(engine)
    existing_cols = [col["name"] for col in insp.get_columns("notifications")]
    print("Existing columns in notifications:", existing_cols)

    columns_to_add = [
        ("recipient_user_id", "INT NULL"),
        ("recipient_role", "VARCHAR(50) NULL"),
        ("related_entity_type", "VARCHAR(50) NULL"),
        ("related_entity_id", "INT NULL"),
        ("action_url", "VARCHAR(255) NULL"),
    ]

    with engine.begin() as conn:
        for col_name, col_type in columns_to_add:
            if col_name not in existing_cols:
                print(f"Adding column `{col_name}` ({col_type}) to `notifications`...")
                conn.execute(text(f"ALTER TABLE `notifications` ADD COLUMN `{col_name}` {col_type};"))
                print(f"[OK] Added `{col_name}`.")
            else:
                print(f"[SKIP] `{col_name}` already exists.")

        # Add index on recipient_user_id if not present
        indexes = [idx["name"] for idx in insp.get_indexes("notifications")]
        if "ix_notifications_recipient_user_id" not in indexes:
            try:
                conn.execute(text("CREATE INDEX ix_notifications_recipient_user_id ON notifications (recipient_user_id);"))
                print("[OK] Created index on recipient_user_id.")
            except Exception as e:
                print("Index creation note:", e)

    # Backfill legacy notifications to admin
    db = SessionLocal()
    try:
        admin_user = db.query(User).filter(User.role == "admin").first()
        admin_id = admin_user.id if admin_user else 1

        with engine.begin() as conn:
            conn.execute(
                text(
                    "UPDATE `notifications` SET `recipient_role` = 'admin', `recipient_user_id` = :admin_id WHERE `recipient_user_id` IS NULL;"
                ),
                {"admin_id": admin_id}
            )
        print(f"[OK] Legacy notifications backfilled to Admin user (ID {admin_id}).")
    finally:
        db.close()

    print("=" * 60)
    print("NOTIFICATIONS MIGRATION COMPLETED SUCCESSFULLY")
    print("=" * 60)


if __name__ == "__main__":
    run_migration()
