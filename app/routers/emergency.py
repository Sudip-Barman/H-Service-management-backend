from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.emergency import EmergencyPatient
from app.schemas.emergency import EmergencyCreate, EmergencyResponse, EmergencyUpdate

router = APIRouter(
    prefix="/api/emergency",
    tags=["Emergency"]
)


def _format_emergency(e: EmergencyPatient) -> dict:
    return {
        "id": e.emergency_code or f"ER-{24000 + e.id}",
        "patient_id": e.id,
        "name": e.name,
        "age": e.age,
        "gender": e.gender,
        "bloodGroup": e.blood_group,
        "blood_group": e.blood_group,
        "phone": e.phone,
        "emergencyContact": e.emergency_contact,
        "emergency_contact": e.emergency_contact,
        "emergencyPhone": e.emergency_phone,
        "emergency_phone": e.emergency_phone,
        "arrivalTime": e.arrival_time,
        "arrival_time": e.arrival_time,
        "triage": e.triage,
        "status": e.status,
        "condition": e.condition_summary,
        "condition_summary": e.condition_summary,
        "symptoms": e.symptoms,
        "assignedDoctor": e.assigned_doctor,
        "assigned_doctor": e.assigned_doctor,
        "department": e.department,
        "room": e.room,
        "allergies": e.allergies,
        "notes": e.notes,
    }


@router.get("")
def get_emergency_patients(db: Session = Depends(get_db)):
    patients = db.query(EmergencyPatient).order_by(EmergencyPatient.id.desc()).all()
    return [_format_emergency(p) for p in patients]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_emergency_patient(data: EmergencyCreate, db: Session = Depends(get_db)):
    existing = db.query(EmergencyPatient).filter(
        EmergencyPatient.emergency_code == data.emergency_code
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Emergency code already exists"
        )

    patient = EmergencyPatient(**data.model_dump())
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return _format_emergency(patient)


@router.put("/{emergency_id}")
def update_emergency_patient(emergency_id: int, data: EmergencyUpdate, db: Session = Depends(get_db)):
    patient = db.query(EmergencyPatient).filter(EmergencyPatient.id == emergency_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Emergency patient record not found"
        )

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(patient, field, value)

    db.commit()
    db.refresh(patient)
    return _format_emergency(patient)


@router.delete("/{emergency_id}")
def delete_emergency_patient(emergency_id: int, db: Session = Depends(get_db)):
    patient = db.query(EmergencyPatient).filter(EmergencyPatient.id == emergency_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Emergency patient record not found"
        )

    db.delete(patient)
    db.commit()
    return {"message": "Emergency patient record deleted"}
