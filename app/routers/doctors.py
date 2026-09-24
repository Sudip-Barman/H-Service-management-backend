import os
import re
import secrets
import uuid
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
from app.models.doctor import Doctor
from app.models.user import User
from app.schemas.doctor import DoctorResponse
from app.core.security import hash_password
from app.services.notification_service import (
    create_system_notification,
    create_targeted_notification,
)
from app.utils.validation import validate_phone_number, validate_dob


router = APIRouter(
    prefix="/api/doctors",
    tags=["Doctors"],
)


# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent.parent

UPLOAD_DIR = BASE_DIR / "uploads" / "doctors"
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

def save_doctor_photo(file: UploadFile) -> str:
    """
    Validate, resize, compress and save a doctor photo.

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
            detail="Doctor photo must be less than 5 MB.",
        )

    try:
        image = Image.open(BytesIO(file_data))

        # Verify that the uploaded content is actually a valid image.
        image.verify()

        # Re-open after verify().
        image = Image.open(BytesIO(file_data))

        # Convert to RGB for WebP/JPEG compatibility.
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

        # Resize while preserving aspect ratio.
        image.thumbnail((512, 512), Image.Resampling.LANCZOS)

        # Generate unique filename.
        filename = f"{uuid.uuid4().hex}.webp"

        file_path = UPLOAD_DIR / filename

        # Save optimized WebP.
        image.save(
            file_path,
            format="WEBP",
            quality=85,
            method=6,
        )

        # Return URL/path, not the image itself.
        return f"/uploads/doctors/{filename}"

    except Exception:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Invalid or corrupted image file.",
        )

    finally:
        file.file.close()


def delete_doctor_photo(photo_path: str | None) -> None:
    """
    Delete an existing doctor photo from disk.
    """

    if not photo_path:
        return

    try:
        filename = Path(photo_path).name

        file_path = UPLOAD_DIR / filename

        if file_path.exists() and file_path.is_file():
            file_path.unlink()

    except Exception:
        # Do not fail the database operation just because
        # an old image could not be removed.
        pass


# ============================================================================
# GET ALL DOCTORS
# ============================================================================

@router.get(
    "",
    response_model=list[DoctorResponse],
)
def get_doctors(
    db: Session = Depends(get_db),
):
    doctors = (
        db.query(Doctor)
        .order_by(Doctor.id.desc())
        .all()
    )
    for doc in doctors:
        if doc.user:
            doc.username = doc.user.username
    return doctors


# ============================================================================
# GET SINGLE DOCTOR
# ============================================================================

@router.get(
    "/{doctor_id}",
    response_model=DoctorResponse,
)
def get_doctor(
    doctor_id: int,
    db: Session = Depends(get_db),
):
    doctor = (
        db.query(Doctor)
        .filter(Doctor.id == doctor_id)
        .first()
    )

    if not doctor:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Doctor not found",
        )

    if doctor.user:
        doctor.username = doctor.user.username

    return doctor


# ============================================================================
# CREATE DOCTOR
# ============================================================================

@router.post(
    "",
    response_model=DoctorResponse,
    status_code=http_status.HTTP_201_CREATED,
)
def create_doctor(
    registration_number: str = Form(...),
    first_name: str = Form(...),
    middle_name: str | None = Form(None),
    last_name: str | None = Form(None),
    date_of_birth: str | None = Form(None),
    gender: str = Form("Male"),
    phone: str = Form(...),
    email: str | None = Form(None),
    address: str | None = Form(None),
    specialization: str = Form(...),
    department: str = Form(...),
    qualification: str | None = Form(None),
    experience_years: int = Form(0),
    consultation_fee: float = Form(0.0),
    license_number: str | None = Form(None),
    license_expiry: str | None = Form(None),
    available_status: str = Form("Available"),
    status: str = Form("Active"),
    photo: UploadFile | None = File(None),
    username: str | None = Form(None),
    temporary_password: str | None = Form(None),
    db: Session = Depends(get_db),
):
    # ------------------------------------------------------------------------
    # Validate username uniqueness if provided
    # ------------------------------------------------------------------------

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

    # ------------------------------------------------------------------------
    # Check duplicate registration number
    # ------------------------------------------------------------------------

    existing = (
        db.query(Doctor)
        .filter(
            Doctor.registration_number == registration_number
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Doctor with this registration number already exists",
        )

    # ------------------------------------------------------------------------
    # Validate phone and DOB
    # ------------------------------------------------------------------------

    try:
        phone = validate_phone_number(phone, "Phone number")
    except ValueError as err:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(err),
        )

    # ------------------------------------------------------------------------
    # Parse dates
    # ------------------------------------------------------------------------

    parsed_dob = None

    if date_of_birth:
        from datetime import date

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

    parsed_license_expiry = None

    if license_expiry:
        from datetime import date

        try:
            parsed_license_expiry = date.fromisoformat(
                license_expiry
            )
        except ValueError:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Invalid license_expiry. Expected YYYY-MM-DD.",
            )

    # ------------------------------------------------------------------------
    # Save photo
    # ------------------------------------------------------------------------

    photo_path = None

    if photo:
        photo_path = save_doctor_photo(photo)

    # ------------------------------------------------------------------------
    # Create doctor
    # ------------------------------------------------------------------------

    doctor = Doctor(
        registration_number=registration_number,
        first_name=first_name,
        middle_name=middle_name,
        last_name=last_name,
        date_of_birth=parsed_dob,
        gender=gender,
        phone=phone,
        email=email,
        address=address,
        specialization=specialization,
        department=department,
        qualification=qualification,
        experience_years=experience_years,
        consultation_fee=consultation_fee,
        license_number=license_number,
        license_expiry=parsed_license_expiry,
        photo=photo_path,
        available_status=available_status,
        status=status,
    )

    try:
        db.add(doctor)
        db.flush()

        # Always automatically generate a unique username and temporary password
        clean_first = re.sub(r'[^a-z0-9]', '', (first_name or '').lower())
        clean_last = re.sub(r'[^a-z0-9]', '', (last_name or '').lower())
        base_u = f"dr_{clean_first}_{clean_last}".strip('_') if clean_last else f"dr_{clean_first}".strip('_')
        if not base_u or base_u == "dr":
            base_u = f"dr_{doctor.id}"

        final_username = base_u
        cnt = 1
        while db.query(User).filter(User.username == final_username).first():
            final_username = f"{base_u}_{secrets.randbelow(900) + 100}"
            cnt += 1

        final_temp_password = f"Doctor@{secrets.randbelow(900) + 100}"

        clean_email = email.strip().lower() if email and email.strip() else f"{final_username}@hospital.com"
        existing_email_user = db.query(User).filter(User.email == clean_email).first()
        if existing_email_user:
            clean_email = f"{final_username}.{doctor.id}@hospital.com"

        doc_full_name = f"Dr. {first_name} {last_name or ''}".strip()
        user_account = User(
            name=doc_full_name,
            username=final_username,
            email=clean_email,
            phone=phone.strip() if phone else None,
            password_hash=hash_password(final_temp_password),
            role="doctor",
            is_active=True,
            must_change_password=True,
        )
        db.add(user_account)
        db.flush()

        doctor.user_id = user_account.id

        # Automated Notification Trigger -> strictly for Administration
        try:
            create_system_notification(
                db=db,
                title=f"New Doctor Registered: {doc_full_name}",
                message=f"{doc_full_name} ({doctor.registration_number}) has been registered in department {doctor.department or 'Medical'} with specialization in {doctor.specialization or 'General Medicine'}.",
                notif_type="Staff",
                priority="Normal",
                department=doctor.department or "Medical",
                recipient="Administration",
                recipient_role="admin",
                recipient_user_id=None,
                related_entity_type="doctor",
                related_entity_id=doctor.id,
                action_url="/admin/doctors",
            )
        except Exception as notif_err:
            print(f"[NOTIFICATION] Warning: Could not create doctor registration notification: {notif_err}")

        db.commit()
        db.refresh(doctor)
        doctor.username = user_account.username
        doctor.temporary_password = final_temp_password

    except Exception:
        db.rollback()

        # If DB insertion fails, don't leave an orphaned image.
        if photo_path:
            delete_doctor_photo(photo_path)

        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create doctor.",
        )

    return doctor


# ============================================================================
# UPDATE DOCTOR
# ============================================================================

@router.put(
    "/{doctor_id}",
    response_model=DoctorResponse,
)
def update_doctor(
    doctor_id: int,
    registration_number: str | None = Form(None),
    first_name: str | None = Form(None),
    middle_name: str | None = Form(None),
    last_name: str | None = Form(None),
    date_of_birth: str | None = Form(None),
    gender: str | None = Form(None),
    phone: str | None = Form(None),
    email: str | None = Form(None),
    address: str | None = Form(None),
    specialization: str | None = Form(None),
    department: str | None = Form(None),
    qualification: str | None = Form(None),
    experience_years: int | None = Form(None),
    consultation_fee: float | None = Form(None),
    license_number: str | None = Form(None),
    license_expiry: str | None = Form(None),
    available_status: str | None = Form(None),
    status: str | None = Form(None),
    photo: UploadFile | None = File(None),
    remove_photo: bool = Form(False),
    username: str | None = Form(None),
    temporary_password: str | None = Form(None),
    db: Session = Depends(get_db),
):
    # ------------------------------------------------------------------------
    # Find doctor
    # ------------------------------------------------------------------------

    doctor = (
        db.query(Doctor)
        .filter(Doctor.id == doctor_id)
        .first()
    )

    if not doctor:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Doctor not found",
        )

    # ------------------------------------------------------------------------
    # Check registration number uniqueness
    # ------------------------------------------------------------------------

    if registration_number and registration_number != doctor.registration_number:
        existing = (
            db.query(Doctor)
            .filter(
                Doctor.registration_number == registration_number,
                Doctor.id != doctor_id,
            )
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Another doctor already uses this registration number.",
            )

        doctor.registration_number = registration_number

    # ------------------------------------------------------------------------
    # Update normal fields
    # ------------------------------------------------------------------------

    if first_name is not None:
        doctor.first_name = first_name

    if middle_name is not None:
        doctor.middle_name = middle_name

    if last_name is not None:
        doctor.last_name = last_name

    if date_of_birth is not None:
        if date_of_birth.strip():
            from datetime import date

            try:
                parsed_dob = date.fromisoformat(date_of_birth.strip())
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
            doctor.date_of_birth = parsed_dob
        else:
            doctor.date_of_birth = None

    if gender is not None:
        doctor.gender = gender

    if phone is not None:
        try:
            doctor.phone = validate_phone_number(phone, "Phone number")
        except ValueError as err:
            raise HTTPException(
                status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(err),
            )

    if email is not None:
        doctor.email = email

    if address is not None:
        doctor.address = address

    if specialization is not None:
        doctor.specialization = specialization

    if department is not None:
        doctor.department = department

    if qualification is not None:
        doctor.qualification = qualification

    if experience_years is not None:
        doctor.experience_years = experience_years

    if consultation_fee is not None:
        doctor.consultation_fee = consultation_fee

    if license_number is not None:
        doctor.license_number = license_number

    if license_expiry is not None:
        from datetime import date

        try:
            doctor.license_expiry = date.fromisoformat(
                license_expiry
            )
        except ValueError:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Invalid license_expiry. Expected YYYY-MM-DD.",
            )

    if available_status is not None:
        doctor.available_status = available_status

    if status is not None:
        doctor.status = status

    # ------------------------------------------------------------------------
    # Replace photo if a new one was uploaded
    # ------------------------------------------------------------------------

    old_photo = doctor.photo
    new_photo = None

    if photo:
        new_photo = save_doctor_photo(photo)
        doctor.photo = new_photo
        if old_photo:
            delete_doctor_photo(old_photo)
    elif remove_photo:
        doctor.photo = None
        if old_photo:
            delete_doctor_photo(old_photo)

    # ------------------------------------------------------------------------
    # Commit
    # ------------------------------------------------------------------------

    try:
        db.commit()
        db.refresh(doctor)

        # Handle updating or creating login credentials
        clean_username = username.strip().lower() if username and username.strip() else None
        if clean_username or temporary_password or doctor.email:
            # Look up existing user by doctor's user_id, email, or username
            existing_user = None
            if doctor.user_id:
                existing_user = db.query(User).filter(User.id == doctor.user_id).first()
            if not existing_user and doctor.email:
                existing_user = db.query(User).filter(User.email == doctor.email.strip().lower()).first()
            if not existing_user and clean_username:
                existing_user = db.query(User).filter(User.username == clean_username).first()

            # Check if username belongs to someone else
            if clean_username:
                user_with_username = db.query(User).filter(User.username == clean_username).first()
                if user_with_username and existing_user and user_with_username.id != existing_user.id:
                    raise HTTPException(
                        status_code=http_status.HTTP_400_BAD_REQUEST,
                        detail=f"Username '{clean_username}' is already taken",
                    )
                elif user_with_username and not existing_user:
                    existing_user = user_with_username

            if existing_user:
                # Update account details while strictly PRESERVING the existing password
                if clean_username:
                    existing_user.username = clean_username
                existing_user.role = "doctor"
                existing_user.is_active = True
                if doctor.phone:
                    existing_user.phone = doctor.phone
                if doctor.email:
                    existing_user.email = doctor.email.strip().lower()
                doc_full_name = f"Dr. {doctor.first_name} {doctor.last_name or ''}".strip()
                existing_user.name = doc_full_name
                doctor.user_id = existing_user.id
            elif clean_username and temporary_password:
                # First-time account creation for this doctor
                if len(temporary_password) < 6:
                    raise HTTPException(
                        status_code=http_status.HTTP_400_BAD_REQUEST,
                        detail="Temporary password must be at least 6 characters long",
                    )
                target_email = doctor.email.strip().lower() if doctor.email else f"{clean_username}@hospital.com"
                if db.query(User).filter(User.email == target_email).first():
                    target_email = f"{clean_username}.{doctor.id}@hospital.com"

                doc_full_name = f"Dr. {doctor.first_name} {doctor.last_name or ''}".strip()
                new_user = User(
                    name=doc_full_name,
                    username=clean_username,
                    email=target_email,
                    phone=doctor.phone,
                    password_hash=hash_password(temporary_password),
                    role="doctor",
                    is_active=True,
                    must_change_password=True,
                )
                db.add(new_user)
                db.flush()
                doctor.user_id = new_user.id
            db.commit()

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()

        # New photo should not remain if DB update failed.
        if new_photo:
            delete_doctor_photo(new_photo)

        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update doctor: {str(e)}",
        )

    # Delete old photo only after successful DB update.
    if new_photo and old_photo and old_photo != new_photo:
        delete_doctor_photo(old_photo)

    return doctor


# ============================================================================
# DELETE DOCTOR
# ============================================================================

@router.delete(
    "/{doctor_id}",
    status_code=http_status.HTTP_200_OK,
)
def delete_doctor(
    doctor_id: int,
    db: Session = Depends(get_db),
):
    doctor = (
        db.query(Doctor)
        .filter(Doctor.id == doctor_id)
        .first()
    )

    if not doctor:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Doctor not found",
        )

    old_photo = doctor.photo

    try:
        db.delete(doctor)
        db.commit()

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete doctor.",
        )

    # Delete image after successful DB deletion.
    if old_photo:
        delete_doctor_photo(old_photo)

    return {
        "message": "Doctor deleted successfully"
    }