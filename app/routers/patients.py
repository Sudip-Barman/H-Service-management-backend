from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.patient import Patient
from app.schemas.patient import (
    PatientCreate,
    PatientResponse,
    PatientUpdate,
)


router = APIRouter(
    prefix="/patients",
    tags=["Patients"]
)


# =========================================================
# REGISTRATION NUMBER GENERATOR
# =========================================================

def generate_registration_number(db: Session) -> str:
    """
    Generate the next patient registration number.

    Format:

        PAT-0001
        PAT-0002
        PAT-0003
        ...

    Existing non-generated registration numbers such as
    BK-123 are ignored.
    """

    patients = (
        db.query(Patient.registration_number)
        .filter(
            Patient.registration_number.like("PAT-%")
        )
        .all()
    )

    highest_number = 0

    for (registration_number,) in patients:

        if not registration_number:
            continue

        try:
            number_part = registration_number.replace(
                "PAT-",
                "",
                1
            )

            number = int(number_part)

            if number > highest_number:
                highest_number = number

        except (ValueError, TypeError):
            continue

    next_number = highest_number + 1

    return f"PAT-{next_number:04d}"


# =========================================================
# CREATE PATIENT
# =========================================================

@router.post(
    "/",
    response_model=PatientResponse,
    status_code=status.HTTP_201_CREATED
)
def create_patient(
    patient_data: PatientCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new patient.

    Registration number is automatically generated.
    """

    # Try a few times in case two users register
    # simultaneously and generate the same number.
    for _ in range(5):

        registration_number = generate_registration_number(db)

        patient = Patient(
            registration_number=registration_number,

            first_name=patient_data.first_name,
            middle_name=patient_data.middle_name,
            last_name=patient_data.last_name,

            date_of_birth=patient_data.date_of_birth,
            age=patient_data.age,

            gender=patient_data.gender,
            blood_group=patient_data.blood_group,

            phone=patient_data.phone,
            email=patient_data.email,

            address=patient_data.address,
            city=patient_data.city,
            state=patient_data.state,
            postal_code=patient_data.postal_code,

            emergency_contact_name=(
                patient_data.emergency_contact_name
            ),

            emergency_contact_phone=(
                patient_data.emergency_contact_phone
            ),

            emergency_contact_relation=(
                patient_data.emergency_contact_relation
            ),

            occupation=patient_data.occupation,
            marital_status=patient_data.marital_status,
            nationality=patient_data.nationality,

            registration_date=(
                patient_data.registration_date
                if patient_data.registration_date
                else None
            ),

            status=patient_data.status,

            patient_problem=patient_data.patient_problem,

            digital_signature=patient_data.digital_signature,
        )

        try:
            db.add(patient)
            db.commit()
            db.refresh(patient)

            return patient

        except IntegrityError:

            # This can happen if another request generated
            # the same registration number at the same moment.
            db.rollback()

            continue

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=(
            "Unable to generate a unique patient "
            "registration number. Please try again."
        )
    )


# =========================================================
# GET ALL PATIENTS
# =========================================================

@router.get(
    "/",
    response_model=list[PatientResponse]
)
def get_patients(
    db: Session = Depends(get_db)
):
    """
    Return all patients.
    """

    return (
        db.query(Patient)
        .order_by(Patient.id.desc())
        .all()
    )


# =========================================================
# GET SINGLE PATIENT
# =========================================================

@router.get(
    "/{patient_id}",
    response_model=PatientResponse
)
def get_patient(
    patient_id: int,
    db: Session = Depends(get_db)
):
    """
    Return one patient by database ID.
    """

    patient = (
        db.query(Patient)
        .filter(Patient.id == patient_id)
        .first()
    )

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found."
        )

    return patient


# =========================================================
# UPDATE PATIENT
# =========================================================

@router.put(
    "/{patient_id}",
    response_model=PatientResponse
)
def update_patient(
    patient_id: int,
    patient_data: PatientUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing patient.

    Registration number cannot be changed.
    """

    patient = (
        db.query(Patient)
        .filter(Patient.id == patient_id)
        .first()
    )

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found."
        )

    update_data = patient_data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(patient, field, value)

    try:
        db.commit()
        db.refresh(patient)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to update patient."
        )

    return patient


# =========================================================
# ARCHIVE / DELETE PATIENT
# =========================================================

@router.delete(
    "/{patient_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_patient(
    patient_id: int,
    db: Session = Depends(get_db)
):
    """
    Permanently delete a patient.

    For normal hospital usage, consider using the PUT endpoint
    with status='Inactive' instead of deleting the record.
    """

    patient = (
        db.query(Patient)
        .filter(Patient.id == patient_id)
        .first()
    )

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found."
        )

    db.delete(patient)
    db.commit()

    return None