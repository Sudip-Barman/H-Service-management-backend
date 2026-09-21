from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.staff import Staff
from app.models.user import User
from app.schemas.staff import StaffCreate, StaffResponse, StaffUpdate
from app.core.dependencies import require_role, require_admin


router = APIRouter(
    prefix="/api/staff",
    tags=["Staff"]
)


@router.get(
    "",
    response_model=list[StaffResponse]
)
def get_staff(
    db: Session = Depends(get_db)
):
    staff = (
        db.query(Staff)
        .order_by(Staff.id.desc())
        .all()
    )

    return staff


@router.get(
    "/{staff_id}",
    response_model=StaffResponse
)
def get_staff_member(
    staff_id: int,
    db: Session = Depends(get_db)
):
    staff = (
        db.query(Staff)
        .filter(Staff.id == staff_id)
        .first()
    )

    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Staff member not found"
        )

    return staff


from app.core.security import hash_password
from app.services.notification_service import create_system_notification


@router.post(
    "",
    response_model=StaffResponse,
    status_code=status.HTTP_201_CREATED
)
def create_staff(
    staff_data: StaffCreate,
    db: Session = Depends(get_db)
):
    clean_username = staff_data.username.strip().lower() if staff_data.username and staff_data.username.strip() else None
    if clean_username:
        if len(clean_username) < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username must be at least 3 characters long",
            )
        existing_user = db.query(User).filter(User.username == clean_username).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Username '{clean_username}' is already taken",
            )
        if staff_data.temporary_password and len(staff_data.temporary_password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Temporary password must be at least 6 characters long",
            )

    new_staff = Staff(
        name=staff_data.name,
        role=staff_data.role,
        gender=staff_data.gender or "Male",
        date_of_birth=staff_data.date_of_birth,
        phone=staff_data.phone,
        email=staff_data.email,
        address=staff_data.address,
        qualification=staff_data.qualification,
        experience=staff_data.experience,
        joining_date=staff_data.joining_date,
        status=staff_data.status
    )

    db.add(new_staff)

    # Automated Notification Trigger
    create_system_notification(
        db=db,
        title=f"New Staff Registered: {new_staff.name}",
        message=f"New staff member {new_staff.name} has been registered as {new_staff.role}.",
        notif_type="Staff",
        priority="Normal",
        department="Human Resources",
        recipient="All Hospital Staff",
    )

    db.commit()
    db.refresh(new_staff)

    # Always ensure a User login account exists for staff
    final_username = clean_username
    if not final_username:
        base_u = f"staff_{new_staff.name.lower().replace(' ', '_')}"
        final_username = base_u
        cnt = 1
        while db.query(User).filter(User.username == final_username).first():
            final_username = f"{base_u}_{new_staff.id}" if cnt == 1 else f"{base_u}_{new_staff.id}_{cnt}"
            cnt += 1

    final_temp_password = staff_data.temporary_password if staff_data.temporary_password and len(staff_data.temporary_password) >= 6 else "TempPass@123"

    clean_email = new_staff.email.strip().lower() if new_staff.email and new_staff.email.strip() else f"{final_username}@hospital.com"
    existing_email_user = db.query(User).filter(User.email == clean_email).first()
    if existing_email_user:
        clean_email = f"{final_username}.{new_staff.id}@hospital.com"

    user_account = User(
        name=new_staff.name,
        username=final_username,
        email=clean_email,
        phone=new_staff.phone.strip() if new_staff.phone else None,
        password_hash=hash_password(final_temp_password),
        role="staff",
        is_active=True,
        must_change_password=True,
    )
    db.add(user_account)
    db.flush()

    new_staff.user_id = user_account.id
    db.commit()
    db.refresh(new_staff)
    new_staff.temporary_password = final_temp_password

    return new_staff


@router.put(
    "/{staff_id}",
    response_model=StaffResponse
)
def update_staff(
    staff_id: int,
    staff_data: StaffUpdate,
    db: Session = Depends(get_db)
):
    staff = (
        db.query(Staff)
        .filter(Staff.id == staff_id)
        .first()
    )

    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Staff member not found"
        )

    update_dict = staff_data.model_dump(exclude_unset=True)
    username = update_dict.pop("username", None)
    temporary_password = update_dict.pop("temporary_password", None)

    for field, value in update_dict.items():
        setattr(staff, field, value)

    clean_username = username.strip().lower() if username and username.strip() else None
    if clean_username or temporary_password:
        existing_user = None
        if staff.email:
            existing_user = db.query(User).filter(User.email == staff.email.strip().lower()).first()
        if not existing_user and clean_username:
            existing_user = db.query(User).filter(User.username == clean_username).first()

        if clean_username:
            user_with_username = db.query(User).filter(User.username == clean_username).first()
            if user_with_username and existing_user and user_with_username.id != existing_user.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Username '{clean_username}' is already taken",
                )
            elif user_with_username and not existing_user:
                existing_user = user_with_username

        if existing_user:
            if clean_username:
                existing_user.username = clean_username
            if temporary_password:
                if len(temporary_password) < 6:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Temporary password must be at least 6 characters long",
                    )
                existing_user.password_hash = hash_password(temporary_password)
                existing_user.must_change_password = True
            existing_user.role = "staff"
            existing_user.is_active = True
            if staff.phone:
                existing_user.phone = staff.phone
            if staff.email:
                existing_user.email = staff.email.strip().lower()
            staff.user_id = existing_user.id
        elif clean_username and temporary_password:
            if len(temporary_password) < 6:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Temporary password must be at least 6 characters long",
                )
            target_email = staff.email.strip().lower() if staff.email else f"{clean_username}@hospital.com"
            if db.query(User).filter(User.email == target_email).first():
                target_email = f"{clean_username}.{staff.id}@hospital.com"

            new_user = User(
                name=staff.name,
                username=clean_username,
                email=target_email,
                phone=staff.phone,
                password_hash=hash_password(temporary_password),
                role="staff",
                is_active=True,
                must_change_password=True,
            )
            db.add(new_user)
            db.flush()
            staff.user_id = new_user.id

    db.commit()
    db.refresh(staff)

    return staff


@router.delete(
    "/{staff_id}"
)
def delete_staff(
    staff_id: int,
    db: Session = Depends(get_db)
):
    staff = (
        db.query(Staff)
        .filter(Staff.id == staff_id)
        .first()
    )

    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Staff member not found"
        )

    db.delete(staff)
    db.commit()

    return {
        "message": "Staff member deleted successfully"
    }