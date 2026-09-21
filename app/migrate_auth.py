"""
Safe, idempotent migration script to refactor authentication to a centralized User model.
- Adds user_id column and foreign key to doctors, nurses, and staff tables if missing.
- Links existing users to workforce profiles.
- Creates User accounts for unlinked workforce profiles with secure hashed temporary password.
- Preserves all existing data (admins, doctors, nurses, staff, bookings, etc.).
"""

import re
from sqlalchemy import inspect, text
from app.database import engine, SessionLocal
from app.models.user import User
from app.models.doctor import Doctor
from app.models.nurse import Nurse
from app.models.staff import Staff
from app.core.security import hash_password


def clean_identifier(name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]", "_", name.lower()).strip("_")
    return cleaned[:30] if cleaned else "user"


def run_migration():
    print("=" * 60)
    print("STARTING AUTHENTICATION CENTRALIZATION MIGRATION")
    print("=" * 60)

    insp = inspect(engine)

    # 1. Check and add user_id column to tables
    for table_name in ["doctors", "nurses", "staff"]:
        existing_cols = [col["name"] for col in insp.get_columns(table_name)]
        if "user_id" not in existing_cols:
            print(f"Adding user_id column and foreign key to `{table_name}`...")
            with engine.begin() as conn:
                conn.execute(text(f"ALTER TABLE `{table_name}` ADD COLUMN user_id INT NULL UNIQUE;"))
                try:
                    conn.execute(text(f"""
                        ALTER TABLE `{table_name}` 
                        ADD CONSTRAINT `fk_{table_name}_user_id` 
                        FOREIGN KEY (user_id) REFERENCES `users`(id) 
                        ON DELETE SET NULL;
                    """))
                except Exception as e:
                    print(f"Note on foreign key creation for `{table_name}`: {e}")
            print(f"[OK] Added user_id to `{table_name}`.")
        else:
            print(f"[OK] `{table_name}` already has user_id column.")

    db = SessionLocal()
    try:
        # 2. Check Admin account
        admin_user = db.query(User).filter(User.role == "admin").first()
        if not admin_user:
            # Fallback to User with ID 1
            user1 = db.query(User).filter(User.id == 1).first()
            if user1:
                user1.role = "admin"
                db.commit()
                admin_user = user1
                print(f"[OK] Set User ID 1 ({user1.email}) role to 'admin'")
            else:
                print("[WARN] No admin account found. Please create an admin account.")
        else:
            print(f"[OK] Verified Admin account: ID={admin_user.id}, Username={admin_user.username}, Email={admin_user.email}")

        default_temp_hash = hash_password("TempPass@123")

        # 3. Migrate Doctors
        print("\n--- Migrating Doctors ---")
        doctors = db.query(Doctor).all()
        for doc in doctors:
            if doc.user_id:
                user = db.query(User).filter(User.id == doc.user_id).first()
                print(f"Doctor ID={doc.id} ({doc.first_name} {doc.last_name}) already linked to User ID={doc.user_id} ({user.username if user else 'Unknown'})")
                continue

            # Check if an existing User matches
            matched_user = None
            if doc.email and admin_user and doc.email.lower() != admin_user.email.lower():
                matched_user = db.query(User).filter(User.email == doc.email.lower()).first()

            if not matched_user:
                doc_code = clean_identifier(f"dr_{doc.first_name}_{doc.last_name or ''}")
                matched_user = db.query(User).filter(User.username == doc_code).first()

            # Check if there is an unlinked doctor user with similar name
            if not matched_user:
                candidates = db.query(User).filter(User.role == "doctor").all()
                for c in candidates:
                    # check if already linked to another doctor
                    other = db.query(Doctor).filter(Doctor.user_id == c.id).first()
                    if not other and doc.first_name.lower() in (c.name or "").lower():
                        matched_user = c
                        break

            if matched_user:
                doc.user_id = matched_user.id
                if matched_user.role != "doctor" and matched_user.id != (admin_user.id if admin_user else None):
                    matched_user.role = "doctor"
                print(f"Linked Doctor ID={doc.id} ({doc.first_name} {doc.last_name}) to existing User ID={matched_user.id} ({matched_user.username})")
            else:
                # Create a new User account
                base_username = clean_identifier(f"dr_{doc.first_name}")
                username = base_username
                counter = 1
                while db.query(User).filter(User.username == username).first():
                    username = f"{base_username}_{doc.id}" if counter == 1 else f"{base_username}_{doc.id}_{counter}"
                    counter += 1

                target_email = doc.email.lower() if doc.email and doc.email.strip() else f"{username}@hospital.com"
                if admin_user and target_email == admin_user.email.lower():
                    target_email = f"{username}@hospital.com"
                if db.query(User).filter(User.email == target_email).first():
                    target_email = f"{username}.{doc.id}@hospital.com"

                new_user = User(
                    name=f"Dr. {doc.first_name} {doc.last_name or ''}".strip(),
                    username=username,
                    email=target_email,
                    phone=doc.phone,
                    password_hash=default_temp_hash,
                    role="doctor",
                    is_active=True,
                    must_change_password=True,
                )
                db.add(new_user)
                db.flush()
                doc.user_id = new_user.id
                print(f"Created new User ID={new_user.id} for Doctor ID={doc.id}: username='{username}', temp_password='TempPass@123'")

        db.commit()

        # 4. Migrate Nurses
        print("\n--- Migrating Nurses ---")
        nurses = db.query(Nurse).all()
        for nurse in nurses:
            if nurse.user_id:
                user = db.query(User).filter(User.id == nurse.user_id).first()
                print(f"Nurse ID={nurse.id} ({nurse.first_name} {nurse.last_name}) already linked to User ID={nurse.user_id}")
                continue

            matched_user = None
            if nurse.email and admin_user and nurse.email.lower() != admin_user.email.lower():
                matched_user = db.query(User).filter(User.email == nurse.email.lower()).first()

            if not matched_user:
                candidates = db.query(User).filter(User.role == "nurse").all()
                for c in candidates:
                    other = db.query(Nurse).filter(Nurse.user_id == c.id).first()
                    if not other and (nurse.first_name.lower() in (c.name or "").lower() or nurse.first_name.lower() in (c.username or "").lower()):
                        matched_user = c
                        break

            if matched_user:
                nurse.user_id = matched_user.id
                print(f"Linked Nurse ID={nurse.id} ({nurse.first_name} {nurse.last_name}) to existing User ID={matched_user.id} ({matched_user.username})")
            else:
                base_username = clean_identifier(f"nurse_{nurse.first_name}")
                username = base_username
                counter = 1
                while db.query(User).filter(User.username == username).first():
                    username = f"{base_username}_{nurse.id}" if counter == 1 else f"{base_username}_{nurse.id}_{counter}"
                    counter += 1

                target_email = nurse.email.lower() if nurse.email and nurse.email.strip() else f"{username}@hospital.com"
                if admin_user and target_email == admin_user.email.lower():
                    target_email = f"{username}@hospital.com"
                if db.query(User).filter(User.email == target_email).first():
                    target_email = f"{username}.{nurse.id}@hospital.com"

                new_user = User(
                    name=f"Nurse {nurse.first_name} {nurse.last_name or ''}".strip(),
                    username=username,
                    email=target_email,
                    phone=nurse.phone,
                    password_hash=default_temp_hash,
                    role="nurse",
                    is_active=True,
                    must_change_password=True,
                )
                db.add(new_user)
                db.flush()
                nurse.user_id = new_user.id
                print(f"Created new User ID={new_user.id} for Nurse ID={nurse.id}: username='{username}', temp_password='TempPass@123'")

        db.commit()

        # 5. Migrate Staff
        print("\n--- Migrating Staff ---")
        staff_list = db.query(Staff).all()
        for st in staff_list:
            if st.user_id:
                print(f"Staff ID={st.id} ({st.name}) already linked to User ID={st.user_id}")
                continue

            matched_user = None
            if st.email and admin_user and st.email.lower() != admin_user.email.lower():
                # Check if this email is already assigned to a doctor or nurse
                matched_user = db.query(User).filter(User.email == st.email.lower()).first()

            if not matched_user:
                candidates = db.query(User).filter(User.role == "staff").all()
                for c in candidates:
                    other = db.query(Staff).filter(Staff.user_id == c.id).first()
                    if not other and st.name.lower() in (c.name or "").lower():
                        matched_user = c
                        break

            if matched_user:
                # Only link if not already linked to another staff
                other_staff = db.query(Staff).filter(Staff.user_id == matched_user.id).first()
                if not other_staff:
                    st.user_id = matched_user.id
                    print(f"Linked Staff ID={st.id} ({st.name}) to existing User ID={matched_user.id} ({matched_user.username})")
                    continue

            # If staff is actually a doctor/nurse seed duplicate, skip creating conflicting user if already represented
            # Check if name starts with "Dr." or role is "Doctor" and doctor exists with same email
            if st.email and db.query(Doctor).filter(Doctor.email == st.email).first():
                doc = db.query(Doctor).filter(Doctor.email == st.email).first()
                if doc.user_id:
                    st.user_id = doc.user_id
                    print(f"Linked Staff record ID={st.id} ({st.name}) to Doctor's User ID={doc.user_id}")
                    continue

            # Create new staff user account
            base_username = clean_identifier(f"staff_{st.name}")
            username = base_username
            counter = 1
            while db.query(User).filter(User.username == username).first():
                username = f"{base_username}_{st.id}" if counter == 1 else f"{base_username}_{st.id}_{counter}"
                counter += 1

            target_email = st.email.lower() if st.email and st.email.strip() else f"{username}@hospital.com"
            if admin_user and target_email == admin_user.email.lower():
                target_email = f"{username}@hospital.com"
            if db.query(User).filter(User.email == target_email).first():
                target_email = f"{username}.{st.id}@hospital.com"

            new_user = User(
                name=st.name.strip(),
                username=username,
                email=target_email,
                phone=st.phone,
                password_hash=default_temp_hash,
                role="staff",
                is_active=True,
                must_change_password=True,
            )
            db.add(new_user)
            db.flush()
            st.user_id = new_user.id
            print(f"Created new User ID={new_user.id} for Staff ID={st.id}: username='{username}', temp_password='TempPass@123'")

        db.commit()
        print("\n" + "=" * 60)
        print("MIGRATION COMPLETED SUCCESSFULLY!")
        print("=" * 60)

    except Exception as e:
        db.rollback()
        print(f"ERROR during migration: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_migration()
