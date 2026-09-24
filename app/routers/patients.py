import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.admission import Admission
from app.models.booking import Booking
from app.models.patient import Patient
from app.models.room_bed import Bed, Room
from app.schemas.patient import (
    PatientCreate,
    PatientResponse,
    PatientUpdate,
)
from app.services.billing_service import generate_bill_for_patient
from app.services.notification_service import create_system_notification
from app.utils.validation import validate_dob


router = APIRouter(
    prefix="/api/patients",
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
# ENRICH PATIENT HELPER
# =========================================================

def _enrich_patient(patient: Patient, db: Session) -> dict:
    """
    Enrich patient model with actual data from admissions and bookings tables.
    """
    # 1. Admission lookup
    admission = (
        db.query(Admission)
        .filter(Admission.patient_id == patient.id)
        .order_by(Admission.id.desc())
        .first()
    )

    admission_status = "Not Admitted"
    room_bed = "Not Assigned"
    room_number = None
    bed_number = None
    ward = None

    if admission:
        admission_status = admission.status or "Admitted"
        if admission_status == "Admitted" and admission.room_bed_id:
            bed = db.query(Bed).filter(Bed.id == admission.room_bed_id).first()
            if bed:
                bed_number = bed.bed_number
                if bed.room_id:
                    room = db.query(Room).filter(Room.id == bed.room_id).first()
                    if room:
                        room_number = room.room_number
                        ward = room.ward
                        if ward and room_number:
                            room_bed = f"{ward} - Room {room_number} / {bed_number}"
                        elif room_number:
                            room_bed = f"Room {room_number} / {bed_number}"
                        else:
                            room_bed = str(bed_number)
                else:
                    room_bed = str(bed_number)
        else:
            room_bed = "Not Assigned"

    # 2. Bookings lookup (activity)
    bookings = (
        db.query(Booking)
        .filter(Booking.patient_id == patient.id)
        .all()
    )

    service_bookings = [
        b for b in bookings
        if b.service_id is not None
        or (b.booking_category and "service" in b.booking_category.lower())
    ]
    appointment_bookings = [
        b for b in bookings
        if b.doctor_id is not None
        or (b.booking_category and any(w in b.booking_category.lower() for w in ["consultation", "checkup", "doctor", "appointment"]))
    ]

    # 3. Patient saved services
    saved_services = []
    if patient.services:
        try:
            parsed = json.loads(patient.services)
            if isinstance(parsed, list):
                saved_services = parsed
            else:
                saved_services = [parsed]
        except Exception:
            saved_services = [s.strip() for s in patient.services.split(",") if s.strip()]

    all_service_keys = set()
    for s in saved_services:
        all_service_keys.add(str(s))
    for b in service_bookings:
        if b.service_id:
            all_service_keys.add(f"srv-{b.service_id}")
        else:
            all_service_keys.add(f"bk-{b.booking_id}")

    service_count = len(all_service_keys)
    appointment_count = len(appointment_bookings)

    # 4. Status determination
    effective_status = patient.status or "Active"
    if admission and admission.status == "Admitted":
        effective_status = "Admitted"
    elif effective_status == "Admitted" and (not admission or admission.status != "Admitted"):
        effective_status = "Discharged" if (admission and admission.status == "Discharged") else "Active"
    elif effective_status in ("Active", "Registered") and (service_bookings or appointment_bookings):
        has_active_booking = any(b.status in ("Scheduled", "Confirmed", "In Progress") for b in bookings)
        if has_active_booking:
            effective_status = "Under Treatment"

    return {
        "id": patient.id,
        "registration_number": patient.registration_number,
        "registration_date": patient.registration_date,
        "status": effective_status,
        "first_name": patient.first_name,
        "middle_name": patient.middle_name,
        "last_name": patient.last_name,
        "date_of_birth": patient.date_of_birth,
        "age": patient.age,
        "gender": patient.gender,
        "blood_group": patient.blood_group,
        "occupation": patient.occupation,
        "marital_status": patient.marital_status,
        "nationality": patient.nationality,
        "phone": patient.phone,
        "email": patient.email,
        "address": patient.address,
        "city": patient.city,
        "state": patient.state,
        "postal_code": patient.postal_code,
        "emergency_contact_name": patient.emergency_contact_name,
        "emergency_contact_phone": patient.emergency_contact_phone,
        "emergency_contact_relation": patient.emergency_contact_relation,
        "patient_problem": patient.patient_problem,
        "services": saved_services,
        "admission_status": admission_status,
        "room_bed": room_bed,
        "room_number": room_number,
        "bed_number": bed_number,
        "ward": ward,
        "service_count": service_count,
        "appointment_count": appointment_count,
        "digital_signature": patient.digital_signature,
        "created_at": patient.created_at,
        "updated_at": patient.updated_at,
    }


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

    if patient_data.date_of_birth is not None:
        try:
            validate_dob(patient_data.date_of_birth, is_staff=False, db=db)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))

    services_val = patient_data.services
    if isinstance(services_val, (list, dict)):
        services_val = json.dumps(services_val)

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

            services=services_val,

            digital_signature=patient_data.digital_signature,
        )

        try:
            db.add(patient)

            # Automated Notification Trigger -> strictly for Administration
            patient_full_name = f"{patient.first_name} {patient.last_name or ''}".strip()
            create_system_notification(
                db=db,
                title=f"New Patient Registered: {patient_full_name}",
                message=f"Patient {patient_full_name} ({patient.registration_number}) has been registered in the system.",
                notif_type="Patients",
                priority="Normal",
                department="OPD",
                recipient="Administration",
                recipient_role="admin",
                recipient_user_id=None,
                related_entity_type="patient",
                related_entity_id=patient.id,
                action_url="/admin/patients",
            )

            # Automated Billing Generation
            try:
                generate_bill_for_patient(patient, db)
            except Exception as bill_err:
                print(f"Failed to auto-generate patient bill: {bill_err}")

            db.commit()
            db.refresh(patient)

            return _enrich_patient(patient, db)

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
    Return all patients with enriched admission and activity data.
    """

    patients = (
        db.query(Patient)
        .order_by(Patient.id.desc())
        .all()
    )

    return [_enrich_patient(p, db) for p in patients]


# =========================================================
# GET SINGLE PATIENT
# =========================================================

@router.get(
    "/{patient_id}",
    response_model=PatientResponse
)
def get_patient(
    patient_id: str,
    db: Session = Depends(get_db)
):
    """
    Return one patient by database ID or registration number with enriched admission and activity data.
    """
    clean_id = patient_id.strip()
    if clean_id.isdigit():
        patient = (
            db.query(Patient)
            .filter(
                (Patient.id == int(clean_id)) |
                (Patient.registration_number == clean_id)
            )
            .first()
        )
    else:
        patient = (
            db.query(Patient)
            .filter(Patient.registration_number == clean_id)
            .first()
        )

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found."
        )

    return _enrich_patient(patient, db)


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

    if patient_data.date_of_birth is not None:
        try:
            validate_dob(patient_data.date_of_birth, is_staff=False, db=db)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))

    update_data = patient_data.model_dump(
        exclude_unset=True
    )

    if "services" in update_data and isinstance(update_data["services"], (list, dict)):
        update_data["services"] = json.dumps(update_data["services"])

    for field, value in update_data.items():
        setattr(patient, field, value)

    try:
        db.commit()
        db.refresh(patient)
        try:
            generate_bill_for_patient(patient, db)
            db.commit()
        except Exception as b_err:
            print(f"Failed to sync patient bill on update: {b_err}")

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to update patient."
        )

    return _enrich_patient(patient, db)


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


# =========================================================
# ROUTE ALIASES & LEGACY PREFIX COMPATIBILITY
# =========================================================

# Ensure both /api/patients and /api/patients/ work without redirects
router.add_api_route("", get_patients, methods=["GET"], response_model=list[PatientResponse], include_in_schema=False)
router.add_api_route("", create_patient, methods=["POST"], response_model=PatientResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)

# Legacy /patients router so requests without /api prefix also succeed
legacy_router = APIRouter(
    prefix="/patients",
    tags=["Patients (Legacy)"]
)
legacy_router.add_api_route("/", get_patients, methods=["GET"], response_model=list[PatientResponse], include_in_schema=False)
legacy_router.add_api_route("", get_patients, methods=["GET"], response_model=list[PatientResponse], include_in_schema=False)
legacy_router.add_api_route("/", create_patient, methods=["POST"], response_model=PatientResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
legacy_router.add_api_route("", create_patient, methods=["POST"], response_model=PatientResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
legacy_router.add_api_route("/{patient_id}", get_patient, methods=["GET"], response_model=PatientResponse, include_in_schema=False)
legacy_router.add_api_route("/{patient_id}", update_patient, methods=["PUT"], response_model=PatientResponse, include_in_schema=False)
legacy_router.add_api_route("/{patient_id}", delete_patient, methods=["DELETE"], status_code=status.HTTP_204_NO_CONTENT, include_in_schema=False)