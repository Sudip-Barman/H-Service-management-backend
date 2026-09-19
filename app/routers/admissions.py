from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.admission import Admission
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.room_bed import Bed, Room
from app.models.staff import Staff
from app.schemas.admission import (
    AdmissionCreate,
    AdmissionResponse,
    AdmissionUpdate,
)

router = APIRouter(
    prefix="/api/admissions",
    tags=["Admissions"]
)


def _format_admission(admission: Admission, db: Session) -> dict:
    patient = db.query(Patient).filter(Patient.id == admission.patient_id).first()
    doctor = db.query(Staff).filter(Staff.id == admission.doctor_id).first()
    if not doctor:
        doctor = db.query(Doctor).filter(Doctor.id == admission.doctor_id).first()

    bed = None
    room = None
    if admission.room_bed_id:
        bed = db.query(Bed).options(joinedload(Bed.room)).filter(Bed.id == admission.room_bed_id).first()
        if bed:
            room = bed.room

    patient_name = None
    patient_reg = None
    if patient:
        patient_name = f"{patient.first_name} {patient.last_name or ''}".strip()
        patient_reg = patient.registration_number

    doctor_name = None
    department = None
    if doctor:
        doctor_name = getattr(doctor, "name", None) or f"{getattr(doctor, 'first_name', '')} {getattr(doctor, 'last_name', '')}".strip()
        department = getattr(doctor, "department", None)

    return {
        "id": admission.id,
        "admission_id": admission.id,
        "admission_number": admission.admission_number,
        "patient_id": admission.patient_id,
        "doctor_id": admission.doctor_id,
        "room_bed_id": admission.room_bed_id,
        "admission_date": admission.admission_date,
        "admission_time": admission.admission_time,
        "admission_type": admission.admission_type,
        "reason": admission.reason,
        "diagnosis": admission.diagnosis,
        "discharge_date": admission.discharge_date,
        "discharge_time": admission.discharge_time,
        "discharge_summary": admission.discharge_summary,
        "discharge_status": admission.discharge_status,
        "status": admission.status,
        "remarks": admission.remarks,
        "patient_name": patient_name,
        "patient_registration_number": patient_reg,
        "doctor_name": doctor_name,
        "department": department or (room.department if room else None),
        "ward": room.ward if room else None,
        "room_number": room.room_number if room else None,
        "bed_number": bed.bed_number if bed else None,
    }


@router.get("")
def get_admissions(db: Session = Depends(get_db)):
    admissions = db.query(Admission).order_by(Admission.id.desc()).all()
    formatted = [_format_admission(a, db) for a in admissions]
    return {
        "admissions": formatted,
        "items": formatted,
        "results": formatted
    }


@router.get("/{admission_id}")
def get_admission(admission_id: int, db: Session = Depends(get_db)):
    admission = db.query(Admission).filter(Admission.id == admission_id).first()
    if not admission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admission not found"
        )
    return _format_admission(admission, db)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_admission(data: AdmissionCreate, db: Session = Depends(get_db)):
    existing = db.query(Admission).filter(
        Admission.admission_number == data.admission_number
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admission number already exists"
        )

    patient = db.query(Patient).filter(Patient.id == data.patient_id).first()
    patient_full_name = f"{patient.first_name} {patient.last_name or ''}".strip() if patient else None
    patient_code = patient.registration_number if patient else None

    admission = Admission(**data.model_dump())
    db.add(admission)

    # Relational link: if bed assigned and status is Admitted, mark bed as Occupied
    if data.room_bed_id and data.status == "Admitted":
        bed = db.query(Bed).filter(Bed.id == data.room_bed_id).first()
        if bed:
            bed.status = "Occupied"
            bed.patient_id = data.patient_id
            bed.patient_name = patient_full_name
            bed.patient_code = patient_code
            bed.admission_date = str(data.admission_date)

    db.commit()
    db.refresh(admission)
    return _format_admission(admission, db)


@router.put("/{admission_id}")
def update_admission(admission_id: int, data: AdmissionUpdate, db: Session = Depends(get_db)):
    admission = db.query(Admission).filter(Admission.id == admission_id).first()
    if not admission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admission not found"
        )

    old_status = admission.status
    old_bed_id = admission.room_bed_id

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(admission, field, value)

    # Relational update: If discharged, free up the bed
    if admission.status == "Discharged" and old_status != "Discharged":
        if not admission.discharge_date:
            admission.discharge_date = date.today()
        target_bed_id = admission.room_bed_id or old_bed_id
        if target_bed_id:
            bed = db.query(Bed).filter(Bed.id == target_bed_id).first()
            if bed:
                bed.status = "Available"
                bed.patient_id = None
                bed.patient_name = None
                bed.patient_code = None
                bed.admission_date = None

    # If re-admitted or bed changed
    elif admission.status == "Admitted" and (old_status != "Admitted" or old_bed_id != admission.room_bed_id):
        if old_bed_id and old_bed_id != admission.room_bed_id:
            old_bed = db.query(Bed).filter(Bed.id == old_bed_id).first()
            if old_bed:
                old_bed.status = "Available"
                old_bed.patient_id = None
                old_bed.patient_name = None

        if admission.room_bed_id:
            patient = db.query(Patient).filter(Patient.id == admission.patient_id).first()
            patient_full_name = f"{patient.first_name} {patient.last_name or ''}".strip() if patient else None
            patient_code = patient.registration_number if patient else None

            new_bed = db.query(Bed).filter(Bed.id == admission.room_bed_id).first()
            if new_bed:
                new_bed.status = "Occupied"
                new_bed.patient_id = admission.patient_id
                new_bed.patient_name = patient_full_name
                new_bed.patient_code = patient_code
                new_bed.admission_date = str(admission.admission_date)

    db.commit()
    db.refresh(admission)
    return _format_admission(admission, db)


@router.delete("/{admission_id}")
def delete_admission(admission_id: int, db: Session = Depends(get_db)):
    admission = db.query(Admission).filter(Admission.id == admission_id).first()
    if not admission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admission not found"
        )

    if admission.room_bed_id and admission.status == "Admitted":
        bed = db.query(Bed).filter(Bed.id == admission.room_bed_id).first()
        if bed:
            bed.status = "Available"
            bed.patient_id = None
            bed.patient_name = None
            bed.patient_code = None

    db.delete(admission)
    db.commit()
    return {"message": "Admission deleted successfully"}
