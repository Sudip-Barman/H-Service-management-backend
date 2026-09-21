from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.nurse import Nurse
from app.schemas.nurse import NurseCreate, NurseResponse, NurseUpdate

router = APIRouter(
    prefix="/api/nurses",
    tags=["Nurses"]
)


@router.get("", response_model=list[NurseResponse])
def get_nurses(db: Session = Depends(get_db)):
    return db.query(Nurse).order_by(Nurse.id.desc()).all()


@router.get("/{nurse_id}", response_model=NurseResponse)
def get_nurse(nurse_id: int, db: Session = Depends(get_db)):
    nurse = db.query(Nurse).filter(Nurse.id == nurse_id).first()
    if not nurse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nurse not found"
        )
    return nurse


from app.models.user import User
from app.core.security import hash_password
from app.services.notification_service import create_system_notification


@router.post("", response_model=NurseResponse, status_code=status.HTTP_201_CREATED)
def create_nurse(data: NurseCreate, db: Session = Depends(get_db)):
    existing = db.query(Nurse).filter(
        Nurse.registration_number == data.registration_number
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nurse with this registration number already exists"
        )

    nurse_data = data.model_dump()
    username = nurse_data.pop("username", None)
    temporary_password = nurse_data.pop("temporary_password", None)

    clean_username = username.strip().lower() if username and username.strip() else None
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
        if temporary_password and len(temporary_password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Temporary password must be at least 6 characters long",
            )

    nurse = Nurse(**nurse_data)
    db.add(nurse)

    # Automated Notification Trigger
    nurse_name = f"{nurse.first_name} {nurse.last_name or ''}".strip()
    create_system_notification(
        db=db,
        title=f"New Nurse Registered: {nurse_name}",
        message=f"Nurse {nurse_name} ({nurse.registration_number}) has been registered in department {nurse.department or 'Nursing'}.",
        notif_type="Staff",
        priority="Normal",
        department=nurse.department or "Nursing",
        recipient="Nursing Team & Admin",
    )

    db.commit()
    db.refresh(nurse)

    # Always ensure a User login account exists for the nurse
    final_username = clean_username
    if not final_username:
        base_u = f"nurse_{nurse.first_name.lower().replace(' ', '_')}"
        final_username = base_u
        cnt = 1
        while db.query(User).filter(User.username == final_username).first():
            final_username = f"{base_u}_{nurse.id}" if cnt == 1 else f"{base_u}_{nurse.id}_{cnt}"
            cnt += 1

    final_temp_password = temporary_password if temporary_password and len(temporary_password) >= 6 else "TempPass@123"

    clean_email = nurse.email.strip().lower() if nurse.email and nurse.email.strip() else f"{final_username}@hospital.com"
    existing_email_user = db.query(User).filter(User.email == clean_email).first()
    if existing_email_user:
        clean_email = f"{final_username}.{nurse.id}@hospital.com"

    user_account = User(
        name=nurse_name,
        username=final_username,
        email=clean_email,
        phone=nurse.phone.strip() if nurse.phone else None,
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
    nurse.temporary_password = final_temp_password

    return nurse


@router.put("/{nurse_id}", response_model=NurseResponse)
def update_nurse(nurse_id: int, data: NurseUpdate, db: Session = Depends(get_db)):
    nurse = db.query(Nurse).filter(Nurse.id == nurse_id).first()
    if not nurse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nurse not found"
        )

    update_dict = data.model_dump(exclude_unset=True)
    username = update_dict.pop("username", None)
    temporary_password = update_dict.pop("temporary_password", None)

    for field, value in update_dict.items():
        setattr(nurse, field, value)

    clean_username = username.strip().lower() if username and username.strip() else None
    if clean_username or temporary_password:
        existing_user = None
        if nurse.email:
            existing_user = db.query(User).filter(User.email == nurse.email.strip().lower()).first()
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
            existing_user.role = "nurse"
            existing_user.is_active = True
            if nurse.phone:
                existing_user.phone = nurse.phone
            if nurse.email:
                existing_user.email = nurse.email.strip().lower()
            nurse.user_id = existing_user.id
        elif clean_username and temporary_password:
            if len(temporary_password) < 6:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Temporary password must be at least 6 characters long",
                )
            target_email = nurse.email.strip().lower() if nurse.email else f"{clean_username}@hospital.com"
            if db.query(User).filter(User.email == target_email).first():
                target_email = f"{clean_username}.{nurse.id}@hospital.com"

            nurse_name = f"{nurse.first_name} {nurse.last_name or ''}".strip()
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
    return nurse


@router.delete("/{nurse_id}", status_code=status.HTTP_200_OK)
def delete_nurse(nurse_id: int, db: Session = Depends(get_db)):
    nurse = db.query(Nurse).filter(Nurse.id == nurse_id).first()
    if not nurse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nurse not found"
        )

    db.delete(nurse)
    db.commit()
    return {"message": "Nurse deleted successfully"}
