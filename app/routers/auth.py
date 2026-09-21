from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User
from app.models.doctor import Doctor
from app.models.nurse import Nurse
from app.models.staff import Staff
from app.schemas.user import (
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
    UserProfileUpdate,
)
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.core.dependencies import get_current_user, require_admin

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)


def get_user_profile(user: User, db: Session) -> dict | None:
    """Fetch the workforce profile associated with a User."""
    if user.role == "doctor":
        doc = db.query(Doctor).filter(Doctor.user_id == user.id).first()
        if doc:
            return {
                "id": doc.id,
                "user_id": doc.user_id,
                "registration_number": doc.registration_number,
                "first_name": doc.first_name,
                "middle_name": doc.middle_name,
                "last_name": doc.last_name,
                "name": f"Dr. {doc.first_name} {doc.last_name or ''}".strip(),
                "gender": doc.gender,
                "date_of_birth": str(doc.date_of_birth) if doc.date_of_birth else None,
                "phone": doc.phone,
                "email": doc.email,
                "address": doc.address,
                "specialization": doc.specialization,
                "department": doc.department,
                "qualification": doc.qualification,
                "experience_years": doc.experience_years,
                "consultation_fee": float(doc.consultation_fee) if doc.consultation_fee else 0.0,
                "license_number": doc.license_number,
                "license_expiry": str(doc.license_expiry) if doc.license_expiry else None,
                "photo": doc.photo,
                "available_status": doc.available_status,
                "status": doc.status,
            }
    elif user.role == "nurse":
        nurse = db.query(Nurse).filter(Nurse.user_id == user.id).first()
        if nurse:
            return {
                "id": nurse.id,
                "user_id": nurse.user_id,
                "nurse_id": nurse.nurse_id,
                "staff_id": nurse.staff_id,
                "registration_number": nurse.registration_number,
                "first_name": nurse.first_name,
                "middle_name": nurse.middle_name,
                "last_name": nurse.last_name,
                "name": f"Nurse {nurse.first_name} {nurse.last_name or ''}".strip(),
                "gender": nurse.gender,
                "date_of_birth": str(nurse.date_of_birth) if nurse.date_of_birth else None,
                "phone": nurse.phone,
                "email": nurse.email,
                "address": nurse.address,
                "department": nurse.department,
                "ward": nurse.ward,
                "qualification": nurse.qualification,
                "experience_years": nurse.experience_years,
                "license_number": nurse.license_number,
                "license_expiry": str(nurse.license_expiry) if nurse.license_expiry else None,
                "shift_type": nurse.shift_type,
                "photo": nurse.photo,
                "status": nurse.status,
            }
    elif user.role == "staff":
        st = db.query(Staff).filter(Staff.user_id == user.id).first()
        if st:
            return {
                "id": st.id,
                "user_id": st.user_id,
                "name": st.name,
                "role": st.role,
                "gender": st.gender,
                "date_of_birth": str(st.date_of_birth) if st.date_of_birth else None,
                "phone": st.phone,
                "email": st.email,
                "address": st.address,
                "qualification": st.qualification,
                "experience": st.experience,
                "joining_date": str(st.joining_date) if st.joining_date else None,
                "status": st.status,
            }
    return None


def serialize_user_with_profile(user: User, db: Session) -> UserResponse:
    """Helper to convert User model into UserResponse with attached profile."""
    profile_data = get_user_profile(user, db)
    return UserResponse(
        id=user.id,
        name=user.name,
        username=user.username,
        email=user.email,
        phone=user.phone,
        avatar=user.avatar,
        role=user.role,
        is_active=user.is_active,
        must_change_password=user.must_change_password,
        profile=profile_data,
    )


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    existing_user = (
        db.query(User)
        .filter(User.email == user_data.email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered"
        )

    new_user = User(
        name=user_data.name,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        role=user_data.role
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return serialize_user_with_profile(new_user, db)


@router.post(
    "/login",
    response_model=TokenResponse
)
def login(
    user_data: UserLogin,
    db: Session = Depends(get_db)
):
    identifier = user_data.email.strip()
    user = (
        db.query(User)
        .filter((User.email == identifier) | (User.username == identifier))
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not verify_password(
        user_data.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # Validate portal option context
    if user_data.role:
        portal = user_data.role.strip().lower()
        if portal == "admin" and user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: This login option is reserved for Administrators only. Please select the Staff / Workforce option."
            )
        elif portal == "staff" and user.role not in ("doctor", "nurse", "staff"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Admin accounts cannot log in through the Staff portal. Please select the Admin option."
            )

    access_token = create_access_token({
        "sub": str(user.id),
        "role": user.role
    })

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": serialize_user_with_profile(user, db)
    }


@router.get(
    "/me",
    response_model=UserResponse
)
def get_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return serialize_user_with_profile(current_user, db)


@router.put(
    "/me",
    response_model=UserResponse
)
@router.put(
    "/profile",
    response_model=UserResponse
)
def update_profile(
    data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check email uniqueness if email changed
    if data.email and data.email.lower() != current_user.email.lower():
        existing = db.query(User).filter(
            User.email == data.email.lower(),
            User.id != current_user.id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This email is already in use by another user"
            )
        current_user.email = data.email.lower()

    # Check username uniqueness if username changed
    if data.username and (not current_user.username or data.username.lower() != current_user.username.lower()):
        existing = db.query(User).filter(
            User.username == data.username.lower(),
            User.id != current_user.id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This username is already taken"
            )
        current_user.username = data.username.lower()

    if data.name is not None:
        current_user.name = data.name.strip()

    if data.phone is not None:
        current_user.phone = data.phone.strip()

    if data.avatar is not None:
        current_user.avatar = data.avatar

    # Crucial: Ensure role and is_active are never modified from profile update
    db.commit()
    db.refresh(current_user)

    return serialize_user_with_profile(current_user, db)


class ChangePasswordRequest(BaseModel):
    current_password: str | None = None
    old_password: str | None = None
    new_password: str
    confirm_password: str | None = None
    confirmPassword: str | None = None
    email: str | None = None


@router.post("/change-password")
def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    current_pwd = data.current_password or data.old_password
    if not current_pwd:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is required"
        )

    confirm_pwd = data.confirm_password or data.confirmPassword
    if confirm_pwd and confirm_pwd != data.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password and confirmation do not match"
        )

    if len(data.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 6 characters long"
        )

    if not verify_password(current_pwd, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    current_user.password_hash = hash_password(data.new_password)
    current_user.must_change_password = False
    db.commit()
    db.refresh(current_user)

    return {
        "message": "Password changed successfully",
        "must_change_password": False,
        "user": serialize_user_with_profile(current_user, db)
    }


class SetEmployeeCredentialsRequest(BaseModel):
    employee_type: str  # "doctor", "nurse", "staff"
    employee_id: int | str
    username: str
    temporary_password: str
    name: str | None = None
    email: str | None = None
    phone: str | None = None


@router.post("/set-employee-credentials")
def set_employee_credentials(
    data: SetEmployeeCredentialsRequest,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    username = data.username.strip().lower()
    if len(username) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username must be at least 3 characters long"
        )

    if len(data.temporary_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Temporary password must be at least 6 characters long"
        )

    role = data.employee_type.strip().lower()
    if role not in ("doctor", "nurse", "staff"):
        role = "staff"

    clean_email = data.email.strip().lower() if data.email and data.email.strip() else None

    # Check if a user matches by username or email
    user = None
    if clean_email:
        user = db.query(User).filter(User.email == clean_email).first()

    if not user:
        user = db.query(User).filter(User.username == username).first()

    # If username is used by a different user
    user_with_username = db.query(User).filter(User.username == username).first()
    if user_with_username and user and user_with_username.id != user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username '{username}' is already taken by another account"
        )
    elif user_with_username and not user:
        user = user_with_username

    hashed_pwd = hash_password(data.temporary_password)

    if user:
        # Update existing user account
        user.username = username
        user.password_hash = hashed_pwd
        user.role = role
        user.is_active = True
        user.must_change_password = True
        if data.name:
            user.name = data.name.strip()
        if data.phone:
            user.phone = data.phone.strip()
        if clean_email:
            user.email = clean_email
    else:
        # Create new user account
        target_email = clean_email or f"{username}@hospital.com"
        existing_email_user = db.query(User).filter(User.email == target_email).first()
        if existing_email_user:
            target_email = f"{username}.{data.employee_id}@hospital.com"

        user = User(
            name=data.name.strip() if data.name else username,
            username=username,
            email=target_email,
            phone=data.phone.strip() if data.phone else None,
            password_hash=hashed_pwd,
            role=role,
            is_active=True,
            must_change_password=True,
        )
        db.add(user)

    db.flush()

    # Link user_id to the specific workforce profile
    try:
        emp_id = int(data.employee_id)
        if role == "doctor":
            doc = db.query(Doctor).filter(Doctor.id == emp_id).first()
            if doc:
                doc.user_id = user.id
        elif role == "nurse":
            nurse = db.query(Nurse).filter(Nurse.id == emp_id).first()
            if nurse:
                nurse.user_id = user.id
        elif role == "staff":
            staff = db.query(Staff).filter(Staff.id == emp_id).first()
            if staff:
                staff.user_id = user.id
    except (ValueError, TypeError):
        pass

    db.commit()
    db.refresh(user)

    return {
        "message": f"Login credentials configured for {username}",
        "username": username,
        "role": role,
        "user_id": user.id,
        "must_change_password": True
    }