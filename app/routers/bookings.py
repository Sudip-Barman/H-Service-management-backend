from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.booking import Booking
from app.schemas.booking import (
    BookingCreate,
    BookingResponse,
    BookingStatusUpdate,
    BookingUpdate,
)

router = APIRouter(
    prefix="/api/bookings",
    tags=["Bookings"],
)


VALID_STATUSES = {
    "Scheduled",
    "Confirmed",
    "Completed",
    "Cancelled",
    "No Show",
}

VALID_PRIORITIES = {
    "Low",
    "Normal",
    "High",
    "Emergency",
}

VALID_BOOKING_TYPES = {
    "In-Person",
    "Online",
    "Home Visit",
}

VALID_PAYMENT_STATUSES = {
    "Pending",
    "Partial",
    "Paid",
    "Refunded",
}


def generate_booking_number(db: Session) -> str:
    last_number = (
        db.query(
            func.max(
                func.cast(
                    func.replace(
                        Booking.booking_number,
                        "BK-",
                        "",
                    ),
                    # MySQL
                    __import__("sqlalchemy").Integer,
                )
            )
        )
        .scalar()
    )

    next_number = (last_number or 1000) + 1

    booking_number = f"BK-{next_number}"

    while (
        db.query(Booking)
        .filter(
            Booking.booking_number == booking_number
        )
        .first()
        is not None
    ):
        next_number += 1
        booking_number = f"BK-{next_number}"

    return booking_number


def validate_booking_values(data):
    if (
        data.status is not None
        and data.status not in VALID_STATUSES
    ):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid booking status: {data.status}",
        )

    if (
        data.priority is not None
        and data.priority not in VALID_PRIORITIES
    ):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid priority: {data.priority}",
        )

    if (
        data.booking_type is not None
        and data.booking_type not in VALID_BOOKING_TYPES
    ):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid booking type: {data.booking_type}",
        )

    if (
        data.payment_status is not None
        and data.payment_status
        not in VALID_PAYMENT_STATUSES
    ):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid payment status: {data.payment_status}",
        )


@router.get(
    "",
    response_model=list[BookingResponse],
)
def get_bookings(
    db: Session = Depends(get_db),
    status: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    payment_status: str | None = Query(default=None),
    booking_date: str | None = Query(default=None),
    search: str | None = Query(default=None),
):
    query = db.query(Booking)

    if status and status != "All":
        query = query.filter(
            Booking.status == status
        )

    if priority and priority != "All":
        query = query.filter(
            Booking.priority == priority
        )

    if (
        payment_status
        and payment_status != "All"
    ):
        query = query.filter(
            Booking.payment_status
            == payment_status
        )

    if booking_date:
        query = query.filter(
            Booking.booking_date
            == booking_date
        )

    if search:
        search_value = f"%{search.strip()}%"

        query = query.filter(
            Booking.booking_number.ilike(
                search_value
            )
            |
            Booking.reason.ilike(
                search_value
            )
        )

    return (
        query.order_by(
            Booking.booking_date.asc(),
            Booking.booking_time.asc(),
            Booking.booking_id.desc(),
        )
        .all()
    )


@router.get(
    "/{booking_id}",
    response_model=BookingResponse,
)
def get_booking(
    booking_id: int,
    db: Session = Depends(get_db),
):
    booking = (
        db.query(Booking)
        .filter(
            Booking.booking_id == booking_id
        )
        .first()
    )

    if not booking:
        raise HTTPException(
            status_code=404,
            detail="Booking not found",
        )

    return booking


from app.models.doctor import Doctor
from app.services.billing_service import generate_bill_for_booking
from app.services.notification_service import (
    create_system_notification,
    create_targeted_notification,
)


def _notify_doctor_booking(booking: Booking, event: str, db: Session):
    if not booking.doctor_id:
        return
    doc = db.query(Doctor).filter(Doctor.id == booking.doctor_id).first()
    if not doc or not doc.user_id:
        return

    p_name = booking.patient_name or "Patient"
    if event == "create":
        title = f"New Appointment: {p_name}"
        msg = f"New appointment ({booking.booking_number}) assigned with {p_name} on {booking.booking_date} at {booking.booking_time}."
        n_type = "appointment_assigned"
    elif event == "cancel":
        title = f"Appointment Cancelled: {p_name}"
        msg = f"Appointment {booking.booking_number} with {p_name} for {booking.booking_date} has been cancelled."
        n_type = "appointment_cancelled"
    else:
        title = f"Appointment Updated: {p_name}"
        msg = f"Appointment {booking.booking_number} with {p_name} has been updated (Date: {booking.booking_date}, Time: {booking.booking_time}, Status: {booking.status})."
        n_type = "appointment_updated"

    create_targeted_notification(
        db=db,
        title=title,
        message=msg,
        recipient_user_id=doc.user_id,
        recipient_role="doctor",
        notif_type=n_type,
        priority="Normal",
        department=doc.department or "Outpatient",
        recipient=f"Dr. {doc.first_name} {doc.last_name or ''}".strip(),
        related_entity_type="appointment",
        related_entity_id=booking.booking_id,
        action_url="/workforce/appointments",
    )


@router.post(
    "",
    response_model=BookingResponse,
    status_code=201,
)
def create_booking(
    data: BookingCreate,
    db: Session = Depends(get_db),
):
    validate_booking_values(data)

    if data.booking_number:
        existing = (
            db.query(Booking)
            .filter(
                Booking.booking_number
                == data.booking_number
            )
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=409,
                detail="Booking number already exists",
            )

        booking_number = data.booking_number
    else:
        booking_number = generate_booking_number(
            db
        )

    booking_dict = data.model_dump()
    booking_dict["booking_number"] = booking_number

    booking = Booking(**booking_dict)
    db.add(booking)
    db.flush()

    # Automated Notification Trigger for Admin/Reception
    p_name = booking.patient_name or "Patient"
    p_priority = "Urgent" if booking.priority in ["Urgent", "Emergency"] else ("High" if booking.priority == "High" else "Normal")
    create_system_notification(
        db=db,
        title=f"New Booking: {p_name}",
        message=f"Booking {booking.booking_number} received for {p_name} ({booking.booking_category or 'Appointment'}). Date: {booking.booking_date or 'TBD'}, Time: {booking.booking_time or 'TBD'}.",
        notif_type="Bookings",
        priority=p_priority,
        department="Reception",
        recipient="Reception & Medical Staff",
        recipient_role="admin",
        related_entity_type="appointment",
        related_entity_id=booking.booking_id,
        action_url="/admin/booking",
    )

    # Targeted Doctor Notification
    _notify_doctor_booking(booking, "create", db)

    # Automated Billing Generation
    try:
        generate_bill_for_booking(booking, db)
    except Exception as bill_err:
        print(f"Failed to auto-generate booking bill: {bill_err}")

    db.commit()
    db.refresh(booking)

    return booking


@router.put(
    "/{booking_id}",
    response_model=BookingResponse,
)
def update_booking(
    booking_id: int,
    data: BookingUpdate,
    db: Session = Depends(get_db),
):
    booking = (
        db.query(Booking)
        .filter(
            Booking.booking_id == booking_id
        )
        .first()
    )

    if not booking:
        raise HTTPException(
            status_code=404,
            detail="Booking not found",
        )

    validate_booking_values(data)

    update_data = data.model_dump(
        exclude_unset=True
    )

    if (
        "booking_number" in update_data
        and update_data["booking_number"]
        and update_data["booking_number"]
        != booking.booking_number
    ):
        existing = (
            db.query(Booking)
            .filter(
                Booking.booking_number
                == update_data["booking_number"],
                Booking.booking_id
                != booking_id,
            )
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=409,
                detail="Booking number already exists",
            )

    for field, value in update_data.items():
        setattr(
            booking,
            field,
            value,
        )

    booking.updated_at = datetime.utcnow()

    # Automated Billing Sync
    try:
        generate_bill_for_booking(booking, db)
    except Exception as bill_err:
        print(f"Failed to update booking bill: {bill_err}")

    # Notify Doctor
    _notify_doctor_booking(booking, "cancel" if booking.status == "Cancelled" else "update", db)

    db.commit()
    db.refresh(booking)

    return booking


@router.patch(
    "/{booking_id}/status",
    response_model=BookingResponse,
)
def update_booking_status(
    booking_id: int,
    data: BookingStatusUpdate,
    db: Session = Depends(get_db),
):
    if data.status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid booking status: {data.status}",
        )

    booking = (
        db.query(Booking)
        .filter(
            Booking.booking_id == booking_id
        )
        .first()
    )

    if not booking:
        raise HTTPException(
            status_code=404,
            detail="Booking not found",
        )

    booking.status = data.status
    booking.updated_at = datetime.utcnow()

    # Notify Doctor
    _notify_doctor_booking(booking, "cancel" if booking.status == "Cancelled" else "update", db)

    db.commit()
    db.refresh(booking)

    return booking


@router.delete(
    "/{booking_id}",
)
def delete_booking(
    booking_id: int,
    db: Session = Depends(get_db),
):
    booking = (
        db.query(Booking)
        .filter(
            Booking.booking_id == booking_id
        )
        .first()
    )

    if not booking:
        raise HTTPException(
            status_code=404,
            detail="Booking not found",
        )

    db.delete(booking)
    db.commit()

    return {
        "message": "Booking deleted successfully",
        "booking_id": booking_id,
    }