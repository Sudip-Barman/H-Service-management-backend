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


from app.services.notification_service import create_targeted_notification
from app.models.user import User
from app.models.doctor import Doctor
from app.models.nurse import Nurse
from app.models.staff import Staff


def _resolve_requester_user(identifier: str | None, db: Session) -> User | None:
    if not identifier:
        return None
    clean = identifier.replace("Dr.", "").replace("Nurse", "").strip()
    u = db.query(User).filter(
        (User.username == clean) | (User.email == clean) | (User.name == clean)
    ).first()
    if u:
        return u
    doc = db.query(Doctor).filter(
        (Doctor.first_name.ilike(f"%{clean}%")) | (Doctor.last_name.ilike(f"%{clean}%"))
    ).first()
    if doc and doc.user_id:
        return db.query(User).filter(User.id == doc.user_id).first()
    nurse = db.query(Nurse).filter(
        (Nurse.first_name.ilike(f"%{clean}%")) | (Nurse.last_name.ilike(f"%{clean}%"))
    ).first()
    if nurse and nurse.user_id:
        return db.query(User).filter(User.id == nurse.user_id).first()
    st = db.query(Staff).filter(Staff.name.ilike(f"%{clean}%")).first()
    if st and st.user_id:
        return db.query(User).filter(User.id == st.user_id).first()
    return db.query(User).filter(User.name.ilike(f"%{clean}%")).first()


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
    db.flush()

    # Automated Notification Trigger -> strictly for Admin
    admin_user = db.query(User).filter(User.role == "admin").first()
    admin_id = admin_user.id if admin_user else 1
    p_level = "Urgent" if req.priority in ["Urgent", "Emergency"] else ("High" if req.priority == "High" else "Normal")
    code_display = req.request_code or f"Request for {req.item}"
    create_targeted_notification(
        db=db,
        title=f"New Request: {req.request_type} - {req.item}",
        message=f"Request {code_display} for '{req.item}' submitted by {req.requested_by or 'Staff'}. Priority: {req.priority}.",
        recipient_user_id=admin_id,
        recipient_role="admin",
        notif_type="request_submitted",
        priority=p_level,
        department=req.department or "Hospital Operations",
        recipient="Administration",
        related_entity_type="request",
        related_entity_id=req.id,
        action_url="/admin/requests",
    )

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

    old_status = req.status
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(req, field, value)

    # Notify requester if status changed to Approved or Rejected
    if old_status != req.status and req.status in ["Approved", "Rejected"]:
        requester_user = _resolve_requester_user(req.requested_by, db)
        if requester_user:
            notif_type = "request_approved" if req.status == "Approved" else "request_rejected"
            action_url = "/workforce/schedule" if req.request_type.lower() in ["schedule", "leave", "shift"] else "/workforce/dashboard"
            create_targeted_notification(
                db=db,
                title=f"Request {req.status}: {req.item}",
                message=f"Your {req.request_type} request for '{req.item}' was {req.status.lower()} by Admin.",
                recipient_user_id=requester_user.id,
                recipient_role=requester_user.role,
                notif_type=notif_type,
                priority="Normal",
                department=req.department or "General",
                recipient=requester_user.name,
                related_entity_type="request",
                related_entity_id=req.id,
                action_url=action_url,
            )

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
