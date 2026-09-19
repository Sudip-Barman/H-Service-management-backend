import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.billing import Bill
from app.schemas.billing import BillCreate, BillResponse, BillUpdate

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
        "type": b.bill_type,
        "description": b.description or "Hospital Service",
        "doctor": b.doctor or "Hospital Medical Team",
        "department": b.department or "General Medicine",
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
        "status": b.payment_status,
        "payment_status": b.payment_status,
        "paymentMethod": b.payment_method or "Cash",
        "payment_method": b.payment_method or "Cash",
        "items": items,
    }


@router.get("")
def get_bills(db: Session = Depends(get_db)):
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
    if paid >= total and total > 0:
        bill.payment_status = "Paid"
    elif paid > 0:
        bill.payment_status = "Partial"
    else:
        bill.payment_status = "Pending"

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
