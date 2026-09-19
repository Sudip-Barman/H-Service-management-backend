from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.patient import Patient
from app.models.request import HospitalRequest
from app.schemas.request import RequestCreate, RequestResponse, RequestUpdate

router = APIRouter(
    prefix="/api/requests",
    tags=["Hospital Requests"]
)


def _format_request(r: HospitalRequest) -> dict:
    return {
        "id": r.request_code or f"REQ-{1000 + r.id}",
        "request_id": r.id,
        "type": r.request_type,
        "item": r.item,
        "requestedFor": r.requested_for or "General Ward",
        "requested_for": r.requested_for,
        "patientId": r.patient_id or "",
        "patient_id": r.patient_id,
        "requestedBy": r.requested_by,
        "requested_by": r.requested_by,
        "department": r.department or "Clinical",
        "priority": r.priority,
        "status": r.status,
        "date": str(r.date),
        "requiredDate": str(r.required_date) if r.required_date else "",
        "required_date": str(r.required_date) if r.required_date else "",
        "description": r.description or "",
    }


@router.get("")
def get_requests(db: Session = Depends(get_db)):
    requests = db.query(HospitalRequest).order_by(HospitalRequest.id.desc()).all()
    return [_format_request(r) for r in requests]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_request(data: RequestCreate, db: Session = Depends(get_db)):
    req_for = data.requested_for
    if data.patient_id and not req_for:
        p = db.query(Patient).filter(
            (Patient.registration_number == data.patient_id) |
            (Patient.id == (int(data.patient_id) if data.patient_id.isdigit() else 0))
        ).first()
        if p:
            req_for = f"{p.first_name} {p.last_name or ''}".strip()

    req = HospitalRequest(
        request_code=data.request_code,
        request_type=data.request_type,
        item=data.item,
        requested_for=req_for,
        patient_id=data.patient_id,
        requested_by=data.requested_by,
        department=data.department,
        priority=data.priority,
        status=data.status,
        date=data.date,
        required_date=data.required_date,
        description=data.description,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return _format_request(req)


@router.put("/{request_id}")
def update_request(request_id: str, data: RequestUpdate, db: Session = Depends(get_db)):
    req = db.query(HospitalRequest).filter(
        (HospitalRequest.request_code == request_id) |
        (HospitalRequest.id == (int(request_id) if request_id.isdigit() else 0))
    ).first()
    if not req:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found"
        )

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(req, field, value)

    db.commit()
    db.refresh(req)
    return _format_request(req)


@router.delete("/{request_id}")
def delete_request(request_id: str, db: Session = Depends(get_db)):
    req = db.query(HospitalRequest).filter(
        (HospitalRequest.request_code == request_id) |
        (HospitalRequest.id == (int(request_id) if request_id.isdigit() else 0))
    ).first()
    if not req:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found"
        )

    db.delete(req)
    db.commit()
    return {"message": "Request deleted successfully"}
