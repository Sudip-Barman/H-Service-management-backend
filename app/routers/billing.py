import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.billing import Bill
from app.models.booking import Booking
from app.schemas.billing import BillCreate, BillResponse, BillUpdate, ManualBillCreate
from app.services.billing_service import create_manual_bill, sync_bills_from_patients_and_bookings

router = APIRouter(
    prefix="/api/billing",
    tags=["Billing & Invoices"]
)


def _format_bill(b: Bill) -> dict:
    items = []
    if b.items_json:
        try:
            items = json.loads(b.items_json)
        except Exception:
            items = []

    subtotal = float(b.subtotal)
    tax = float(b.tax)
    discount = float(b.discount)
    total_amount = float(b.total_amount)
    paid_amount = float(b.paid_amount)
    balance = max(0.0, total_amount - paid_amount)

    # Resolve service name and ID from items or description
    service_name = b.description or "General Service"
    service_id = None
    if items and isinstance(items, list) and len(items) > 0:
        first_item = items[0]
        if isinstance(first_item, dict):
            service_name = first_item.get("service_name") or first_item.get("category") or service_name
            service_id = first_item.get("service_id")

    return {
        "id": b.invoice_number,
        "bill_id": b.id,
        "invoiceNumber": b.invoice_number,
        "patientId": b.patient_id or f"PAT-{1000 + b.id}",
        "patientName": b.patient_name,
        "patientAge": b.patient_age or 35,
        "patientGender": b.patient_gender or "Male",
        "patientPhone": b.patient_phone or "",
        "patientEmail": b.patient_email or "",
        "address": b.address or "",
        "type": b.bill_type or "Service",
        "serviceName": service_name,
        "serviceId": service_id,
        "description": b.description or service_name,
        "department": "HomeCare",
        "visitDate": str(b.date),
        "date": str(b.date),
        "subtotal": subtotal,
        "tax": tax,
        "discount": discount,
        "totalAmount": total_amount,
        "total_amount": total_amount,
        "paidAmount": paid_amount,
        "paid_amount": paid_amount,
        "balance": balance,
        "status": "Paid" if (balance <= 0.01 and total_amount > 0 and paid_amount > 0) else "Due",
        "payment_status": "Paid" if (balance <= 0.01 and total_amount > 0 and paid_amount > 0) else "Due",
        "paymentMethod": b.payment_method or "Cash",
        "payment_method": b.payment_method or "Cash",
        "source": getattr(b, "source", None) or "booking",
        "booking_id": getattr(b, "booking_id", None),
        "bookingId": getattr(b, "booking_id", None),
        "items": items,
    }


@router.get("")
def get_bills(db: Session = Depends(get_db)):
    try:
        sync_bills_from_patients_and_bookings(db)
    except Exception as e:
        print(f"Error syncing bills: {e}")
    bills = db.query(Bill).order_by(Bill.id.desc()).all()
    return [_format_bill(b) for b in bills]


@router.get("/{invoice_number}")
def get_bill(invoice_number: str, db: Session = Depends(get_db)):
    bill = db.query(Bill).filter(
        (Bill.invoice_number == invoice_number) | (Bill.id == (int(invoice_number) if invoice_number.isdigit() else 0))
    ).first()
    if not bill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    return _format_bill(bill)


@router.post("/manual", status_code=status.HTTP_201_CREATED)
def create_manual_bill_endpoint(data: ManualBillCreate, db: Session = Depends(get_db)):
    bill = create_manual_bill(data, db)
    return _format_bill(bill)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_bill(data: BillCreate, db: Session = Depends(get_db)):
    existing = db.query(Bill).filter(Bill.invoice_number == data.invoice_number).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invoice number already exists"
        )

    bill = Bill(**data.model_dump())
    db.add(bill)
    db.commit()
    db.refresh(bill)
    return _format_bill(bill)



@router.put("/{bill_id}")
def update_bill(bill_id: str, data: BillUpdate, db: Session = Depends(get_db)):
    bill = db.query(Bill).filter(
        (Bill.invoice_number == bill_id) | (Bill.id == (int(bill_id) if bill_id.isdigit() else 0))
    ).first()
    if not bill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bill not found"
        )

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(bill, field, value)

    # Re-evaluate payment status
    total = float(bill.total_amount)
    paid = float(bill.paid_amount)
    if total > 0 and paid >= (total - 0.01):
        bill.payment_status = "Paid"
    elif paid > 0:
        bill.payment_status = "Due"  # partial
    else:
        bill.payment_status = "Due"

    db.commit()

    # Sync booking payment_status if this bill is linked to a booking
    booking_id = getattr(bill, "booking_id", None)
    if booking_id:
        booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
        if booking:
            if total > 0 and paid >= (total - 0.01):
                booking.payment_status = "Paid"
            elif paid > 0:
                booking.payment_status = "Partial"
            else:
                booking.payment_status = "Pending"
            db.commit()

    db.refresh(bill)
    return _format_bill(bill)


@router.delete("/{bill_id}")
def delete_bill(bill_id: str, db: Session = Depends(get_db)):
    bill = db.query(Bill).filter(
        (Bill.invoice_number == bill_id) | (Bill.id == (int(bill_id) if bill_id.isdigit() else 0))
    ).first()
    if not bill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bill not found"
        )

    db.delete(bill)
    db.commit()
    return {"message": "Bill deleted successfully"}
