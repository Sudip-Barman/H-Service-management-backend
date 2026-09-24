import os
import re
import secrets
import uuid
from datetime import date
from io import BytesIO
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status as http_status,
)
from PIL import Image
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.nurse import Nurse
from app.models.user import User
from app.schemas.nurse import NurseResponse
from app.core.security import hash_password
from app.services.notification_service import create_system_notification
from app.utils.validation import validate_phone_number, validate_dob

router = APIRouter(
    prefix="/api/nurses",
    tags=["Nurses"],
)

# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent.parent

UPLOAD_DIR = BASE_DIR / "uploads" / "nurses"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/pjpeg",
    "image/png",
    "image/x-png",
    "image/webp",
}


# ============================================================================
# IMAGE HELPERS
# ============================================================================

def save_nurse_photo(file: UploadFile) -> str:
    """
    Validate, resize, compress and save a nurse photo.
    Returns the relative URL path stored in the database.
    """
    if not file:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Photo file is required.",
        )

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Only JPG, PNG and WEBP images are allowed.",
        )

    try:
        file_data = file.file.read()
    except Exception:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Unable to read uploaded photo.",
        )

    if not file_data:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Uploaded photo is empty.",
        )

    if len(file_data) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Nurse photo must be less than 5 MB.",
        )

    try:
        image = Image.open(BytesIO(file_data))
        image.verify()
        image = Image.open(BytesIO(file_data))

        if image.mode in ("RGBA", "LA", "P"):
            background = Image.new("RGB", image.size, "white")
            if image.mode == "P":
                image = image.convert("RGBA")
            background.paste(
                image,
                mask=image.getchannel("A") if image.mode == "RGBA" else None,
            )
            image = background
        else:
            image = image.convert("RGB")

        image.thumbnail((512, 512), Image.Resampling.LANCZOS)
        filename = f"{uuid.uuid4().hex}.webp"
        file_path = UPLOAD_DIR / filename

        image.save(
            file_path,
            format="WEBP",
            quality=85,
            method=6,
        )

        return f"/uploads/nurses/{filename}"

    except Exception:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Invalid or corrupted image file.",
        )
    finally:
        file.file.close()


def delete_nurse_photo(photo_path: str | None) -> None:
    """
    Delete an existing nurse photo from disk if it resides in /uploads/nurses/.
    """
    if not photo_path or not photo_path.startswith("/uploads/nurses/"):
        return

    try:
        filename = Path(photo_path).name
        file_path = UPLOAD_DIR / filename
        if file_path.exists() and file_path.is_file():
            file_path.unlink()
    except Exception:
        pass


# ============================================================================
# GET ALL NURSES
# ============================================================================

@router.get("", response_model=list[NurseResponse])
def get_nurses(db: Session = Depends(get_db)):
    nurses = db.query(Nurse).order_by(Nurse.id.desc()).all()
    for nurse in nurses:
        if nurse.user:
            nurse.username = nurse.user.username
    return nurses


# ============================================================================
# GET SINGLE NURSE
# ============================================================================

@router.get("/{nurse_id}", response_model=NurseResponse)
def get_nurse(nurse_id: int, db: Session = Depends(get_db)):
    nurse = db.query(Nurse).filter(Nurse.id == nurse_id).first()
    if not nurse:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Nurse not found",
        )
    if nurse.user:
        nurse.username = nurse.user.username
    return nurse


# ============================================================================
# CREATE NURSE
# ============================================================================

@router.post(
    "",
    response_model=NurseResponse,
    status_code=http_status.HTTP_201_CREATED,
)
def create_nurse(
    registration_number: str = Form(...),
    first_name: str = Form(...),
    middle_name: str | None = Form(None),
    last_name: str | None = Form(None),
    date_of_birth: str | None = Form(None),
    gender: str = Form("Female"),
    phone: str = Form(...),
    email: str | None = Form(None),
    address: str | None = Form(None),
    qualification: str | None = Form(None),
    department: str = Form(...),
    ward: str | None = Form(None),
    experience_years: int = Form(0),
    license_number: str | None = Form(None),
    license_expiry: str | None = Form(None),
    shift_type: str = Form("Morning"),
    status: str = Form("Active"),
    photo: UploadFile | None = File(None),
    username: str | None = Form(None),
    temporary_password: str | None = Form(None),
    db: Session = Depends(get_db),
):
    # Validate username uniqueness if provided
    clean_username = username.strip().lower() if username and username.strip() else None
    if clean_username:
        if len(clean_username) < 3:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Username must be at least 3 characters long",
            )
        existing_user = db.query(User).filter(User.username == clean_username).first()
        if existing_user:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"Username '{clean_username}' is already taken",
            )
        if temporary_password and len(temporary_password) < 6:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Temporary password must be at least 6 characters long",
            )

    # Check duplicate registration number
    existing = db.query(Nurse).filter(Nurse.registration_number == registration_number).first()
    if existing:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Nurse with this registration number already exists",
        )

    # Validate phone
    try:
        phone = validate_phone_number(phone, "Phone number")
    except ValueError as err:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(err),
        )

    # Parse and validate DOB
    parsed_dob = None
    if date_of_birth:
        try:
            parsed_dob = date.fromisoformat(date_of_birth)
        except ValueError:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Invalid date_of_birth. Expected YYYY-MM-DD.",
            )
        try:
            validate_dob(parsed_dob, is_staff=True, db=db)
        except ValueError as err:
            raise HTTPException(
                status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(err),
            )

    # Parse license expiry
    parsed_license_expiry = None
    if license_expiry:
        try:
            parsed_license_expiry = date.fromisoformat(license_expiry)
        except ValueError:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Invalid license_expiry. Expected YYYY-MM-DD.",
            )

    # Save photo to disk
    photo_path = None
    if photo:
        photo_path = save_nurse_photo(photo)

    nurse = Nurse(
        registration_number=registration_number,
        first_name=first_name,
        middle_name=middle_name,
        last_name=last_name,
        date_of_birth=parsed_dob,
        gender=gender,
        phone=phone,
        email=email,
        address=address,
        qualification=qualification,
        department=department,
        ward=ward,
        experience_years=experience_years,
        license_number=license_number,
        license_expiry=parsed_license_expiry,
        shift_type=shift_type,
        photo=photo_path,
        status=status,
    )

    try:
        db.add(nurse)
        db.flush()

        # Automated Notification Trigger -> strictly for Administration
        nurse_name = f"{nurse.first_name} {nurse.last_name or ''}".strip()
        try:
            create_system_notification(
                db=db,
                title=f"New Nurse Registered: {nurse_name}",
                message=f"Nurse {nurse_name} ({nurse.registration_number}) has been registered in department {nurse.department or 'Nursing'}.",
                notif_type="Staff",
                priority="Normal",
                department=nurse.department or "Nursing",
                recipient="Administration",
                recipient_role="admin",
                recipient_user_id=None,
                related_entity_type="nurse",
                related_entity_id=nurse.id,
                action_url="/admin/staff",
            )
        except Exception as notif_err:
            print(f"[NOTIFICATION] Warning: Could not create nurse notification: {notif_err}")

        # Generate unique username and temporary password
        clean_first = re.sub(r'[^a-z0-9]', '', (first_name or '').lower())
        clean_last = re.sub(r'[^a-z0-9]', '', (last_name or '').lower())
        base_u = f"nurse_{clean_first}_{clean_last}".strip('_') if clean_last else f"nurse_{clean_first}".strip('_')
        if not base_u or base_u == "nurse":
            base_u = f"nurse_{nurse.id}"

        final_username = clean_username or base_u
        if not clean_username:
            cnt = 1
            while db.query(User).filter(User.username == final_username).first():
                final_username = f"{base_u}_{secrets.randbelow(900) + 100}"
                cnt += 1

        final_temp_password = temporary_password or f"Nurse@{secrets.randbelow(900) + 100}"

        clean_email = email.strip().lower() if email and email.strip() else f"{final_username}@hospital.com"
        existing_email_user = db.query(User).filter(User.email == clean_email).first()
        if existing_email_user:
            clean_email = f"{final_username}.{nurse.id}@hospital.com"

        user_account = User(
            name=nurse_name,
            username=final_username,
            email=clean_email,
            phone=phone.strip() if phone else None,
            password_hash=hash_password(final_temp_password),
            role="nurse",
            is_active=True,
            must_change_password=True,
        )
        db.add(user_account)
        db.flush()

        nurse.user_id = user_account.id
        db.commit()
        db.refresh(nurse)
        nurse.username = user_account.username
        nurse.temporary_password = final_temp_password

    except Exception:
        db.rollback()
        if photo_path:
            delete_nurse_photo(photo_path)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create nurse.",
        )

    return nurse


# ============================================================================
# UPDATE NURSE
# ============================================================================

@router.put(
    "/{nurse_id}",
    response_model=NurseResponse,
)
def update_nurse(
    nurse_id: int,
    registration_number: str | None = Form(None),
    first_name: str | None = Form(None),
    middle_name: str | None = Form(None),
    last_name: str | None = Form(None),
    date_of_birth: str | None = Form(None),
    gender: str | None = Form(None),
    phone: str | None = Form(None),
    email: str | None = Form(None),
    address: str | None = Form(None),
    qualification: str | None = Form(None),
    department: str | None = Form(None),
    ward: str | None = Form(None),
    experience_years: int | None = Form(None),
    license_number: str | None = Form(None),
    license_expiry: str | None = Form(None),
    shift_type: str | None = Form(None),
    status: str | None = Form(None),
    photo: UploadFile | None = File(None),
    remove_photo: bool = Form(False),
    username: str | None = Form(None),
    temporary_password: str | None = Form(None),
    db: Session = Depends(get_db),
):
    nurse = db.query(Nurse).filter(Nurse.id == nurse_id).first()
    if not nurse:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Nurse not found",
        )

    # Photo handling
    if remove_photo:
        delete_nurse_photo(nurse.photo)
        nurse.photo = None
    elif photo:
        new_photo_path = save_nurse_photo(photo)
        delete_nurse_photo(nurse.photo)
        nurse.photo = new_photo_path

    # Registration number check if updating
    if registration_number and registration_number != nurse.registration_number:
        existing = db.query(Nurse).filter(
            Nurse.registration_number == registration_number,
            Nurse.id != nurse_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Nurse with this registration number already exists",
            )
        nurse.registration_number = registration_number

    # Phone validation
    if phone:
        try:
            nurse.phone = validate_phone_number(phone, "Phone number")
        except ValueError as err:
            raise HTTPException(
                status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(err),
            )

    # DOB validation
    if date_of_birth is not None:
        if date_of_birth == "":
            nurse.date_of_birth = None
        else:
            try:
                parsed_dob = date.fromisoformat(date_of_birth)
            except ValueError:
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date_of_birth. Expected YYYY-MM-DD.",
                )
            try:
                validate_dob(parsed_dob, is_staff=True, db=db)
                nurse.date_of_birth = parsed_dob
            except ValueError as err:
                raise HTTPException(
                    status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=str(err),
                )

    # License expiry
    if license_expiry is not None:
        if license_expiry == "":
            nurse.license_expiry = None
        else:
            try:
                nurse.license_expiry = date.fromisoformat(license_expiry)
            except ValueError:
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail="Invalid license_expiry. Expected YYYY-MM-DD.",
                )

    if first_name is not None:
        nurse.first_name = first_name
    if middle_name is not None:
        nurse.middle_name = middle_name or None
    if last_name is not None:
        nurse.last_name = last_name or None
    if gender is not None:
        nurse.gender = gender
    if email is not None:
        nurse.email = email or None
    if address is not None:
        nurse.address = address or None
    if qualification is not None:
        nurse.qualification = qualification or None
    if department is not None:
        nurse.department = department
    if ward is not None:
        nurse.ward = ward or None
    if experience_years is not None:
        nurse.experience_years = experience_years
    if license_number is not None:
        nurse.license_number = license_number or None
    if shift_type is not None:
        nurse.shift_type = shift_type
    if status is not None:
        nurse.status = status

    # User Account sync
    clean_username = username.strip().lower() if username and username.strip() else None
    if clean_username or temporary_password or nurse.email:
        existing_user = None
        if nurse.user_id:
            existing_user = db.query(User).filter(User.id == nurse.user_id).first()
        if not existing_user and nurse.email:
            existing_user = db.query(User).filter(User.email == nurse.email.strip().lower()).first()
        if not existing_user and clean_username:
            existing_user = db.query(User).filter(User.username == clean_username).first()

        if clean_username:
            user_with_username = db.query(User).filter(User.username == clean_username).first()
            if user_with_username and existing_user and user_with_username.id != existing_user.id:
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail=f"Username '{clean_username}' is already taken",
                )
            elif user_with_username and not existing_user:
                existing_user = user_with_username

        nurse_name = f"{nurse.first_name} {nurse.last_name or ''}".strip()
        if existing_user:
            if clean_username:
                existing_user.username = clean_username
            existing_user.role = "nurse"
            existing_user.is_active = True
            if nurse.phone:
                existing_user.phone = nurse.phone
            if nurse.email:
                existing_user.email = nurse.email.strip().lower()
            existing_user.name = nurse_name
            nurse.user_id = existing_user.id
        elif clean_username and temporary_password:
            if len(temporary_password) < 6:
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail="Temporary password must be at least 6 characters long",
                )
            target_email = nurse.email.strip().lower() if nurse.email else f"{clean_username}@hospital.com"
            if db.query(User).filter(User.email == target_email).first():
                target_email = f"{clean_username}.{nurse.id}@hospital.com"

            new_user = User(
                name=nurse_name,
                username=clean_username,
                email=target_email,
                phone=nurse.phone,
                password_hash=hash_password(temporary_password),
                role="nurse",
                is_active=True,
                must_change_password=True,
            )
            db.add(new_user)
            db.flush()
            nurse.user_id = new_user.id

    db.commit()
    db.refresh(nurse)
    if nurse.user:
        nurse.username = nurse.user.username
    return nurse


# ============================================================================
# DELETE NURSE
# ============================================================================

@router.delete("/{nurse_id}", status_code=http_status.HTTP_200_OK)
def delete_nurse(nurse_id: int, db: Session = Depends(get_db)):
    nurse = db.query(Nurse).filter(Nurse.id == nurse_id).first()
    if not nurse:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Nurse not found",
        )

    delete_nurse_photo(nurse.photo)
    db.delete(nurse)
    db.commit()
    return {"message": "Nurse deleted successfully"}
