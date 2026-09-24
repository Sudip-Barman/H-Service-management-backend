import json
from datetime import date
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.billing import Bill
from app.models.booking import Booking
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.service import Service
from app.models.settings import HospitalSetting
from app.models.staff import Staff
from app.schemas.billing import ManualBillCreate


def get_hospital_tax_rate(db: Session) -> float:
    try:
        setting = db.query(HospitalSetting).filter(HospitalSetting.key == "billingTaxRate").first()
        if setting and setting.value:
            try:
                val = json.loads(setting.value)
                return float(val)
            except Exception:
                return float(setting.value)
    except Exception:
        pass
    return 5.0


def clean_legacy_dummy_bills(db: Session):
    """Remove hardcoded initial dummy bills and bills for registered patients who took no services."""
    dummy_bills = db.query(Bill).filter(
        (Bill.invoice_number == "INV-2026-001") |
        (Bill.patient_name == "Rahul Sharma")
    ).all()
    if dummy_bills:
        for b in dummy_bills:
            db.delete(b)
        db.commit()

    # Clean up any phantom/legacy bills for patients who took no services
    pat_bills = db.query(Bill).filter(Bill.invoice_number.like("INV-PAT-%")).all()
    for b in pat_bills:
        reg_num = b.invoice_number.replace("INV-", "")
        patient = db.query(Patient).filter(Patient.registration_number == reg_num).first()
        if not patient:
            if float(b.paid_amount or 0.0) <= 0.0:
                db.delete(b)
        else:
            has_services = False
            if patient.services:
                try:
                    parsed = json.loads(patient.services)
                    if isinstance(parsed, list) and len(parsed) > 0:
                        has_services = True
                    elif isinstance(parsed, (int, str)) and str(parsed).strip() and str(parsed).strip() not in ["[]", "{}"]:
                        has_services = True
                except Exception:
                    if patient.services.strip() and patient.services.strip() not in ["[]", "{}"]:
                        has_services = True
            if not has_services and float(b.paid_amount or 0.0) <= 0.0:
                db.delete(b)
    db.commit()


def generate_bill_for_booking(booking: Booking, db: Session) -> Bill:
    """
    Generate or update a bill corresponding to a service booking.
    Prevents duplicate billing for the same booking using booking_id.
    """
    inv_num = f"INV-{booking.booking_number}"
    bill = db.query(Bill).filter(
        (Bill.booking_id == booking.booking_id) | (Bill.invoice_number == inv_num)
    ).first()

    # Find service details
    service = None
    if booking.service_id:
        service = db.query(Service).filter(Service.id == booking.service_id).first()

    # If no service by id, check by booking_category
    if not service and booking.booking_category:
        service = db.query(Service).filter(
            Service.name.ilike(f"%{booking.booking_category}%")
        ).first()

    service_name = service.name if service else (booking.booking_category or "Hospital Service")
    service_id = service.id if service else booking.service_id

    # Determine department (HomeCare for home visit bookings, otherwise service category)
    is_home_care = (
        (booking.service_location_type and "home" in booking.service_location_type.lower()) or
        (booking.booking_type and "home" in booking.booking_type.lower()) or
        (booking.booking_category and "home" in booking.booking_category.lower()) or
        (service and "home" in (service.category or "").lower())
    )
    department = "HomeCare" if is_home_care else (service.category if service else (booking.booking_category or "General Services"))

    # Determine amount & tax using hospital setting
    total_fee = float(booking.total_fee if booking.total_fee is not None and float(booking.total_fee) > 0 else (booking.consultation_fee if booking.consultation_fee else (service.price if service else 500.0)))
    tax_rate = get_hospital_tax_rate(db)
    tax = round(total_fee * (tax_rate / 100.0), 2)
    subtotal = round(total_fee - tax, 2) if total_fee >= tax else total_fee

    payment_status = booking.payment_status or "Pending"
    paid_amount = total_fee if payment_status.lower() == "paid" else 0.0

    # Resolve Staff / Doctor name (Do not assign doctor when no doctor was assigned in booking)
    doctor_name = ""
    if booking.doctor_id:
        doc = db.query(Doctor).filter(Doctor.id == booking.doctor_id).first()
        if doc:
            doctor_name = f"Dr. {doc.first_name} {doc.last_name or ''}".strip()
    elif booking.assigned_staff_id:
        st = db.query(Staff).filter(Staff.id == booking.assigned_staff_id).first()
        if st:
            doctor_name = st.name

    # Patient lookup if patient_id is present
    patient_id_str = f"PAT-{booking.patient_id:04d}" if booking.patient_id else "PAT-OPD"
    patient_age = "35"
    patient_gender = "Not Specified"
    patient_phone = booking.patient_phone or ""
    patient_email = booking.patient_email or ""
    patient_address = booking.patient_address or booking.service_address or ""

    if booking.patient_id:
        patient_obj = db.query(Patient).filter(Patient.id == booking.patient_id).first()
        if patient_obj:
            patient_id_str = patient_obj.registration_number or patient_id_str
            if patient_obj.age:
                patient_age = str(patient_obj.age)
            if patient_obj.gender:
                patient_gender = patient_obj.gender
            if not patient_phone and patient_obj.phone:
                patient_phone = patient_obj.phone
            if not patient_email and patient_obj.email:
                patient_email = patient_obj.email
            if not patient_address and patient_obj.address:
                patient_address = patient_obj.address

    patient_name = booking.patient_name or "Hospital Patient"

    duration_label = ""
    if booking.service_duration:
        duration_label = f" ({booking.service_duration} {booking.service_duration_unit or 'Day'})"

    items = [
        {
            "description": f"{service_name}{duration_label}",
            "category": department or "Service",
            "service_name": service_name,
            "service_id": service_id,
            "quantity": float(booking.service_duration) if (booking.service_duration and float(booking.service_duration) > 0) else 1,
            "rate": float(booking.service_rate if (booking.service_rate and float(booking.service_rate) > 0) else total_fee),
            "unitPrice": float(booking.service_rate if (booking.service_rate and float(booking.service_rate) > 0) else total_fee),
            "amount": total_fee,
            "discount": 0,
        }
    ]

    bill_date = booking.booking_date if booking.booking_date else date.today()

    if not bill:
        bill = Bill(
            invoice_number=inv_num,
            patient_id=patient_id_str,
            patient_name=patient_name,
            patient_age=patient_age,
            patient_gender=patient_gender,
            patient_phone=patient_phone,
            patient_email=patient_email,
            address=patient_address,
            bill_type="Service",
            description=service_name,
            doctor=doctor_name,
            department=department,
            date=bill_date,
            subtotal=subtotal,
            tax=tax,
            discount=0.0,
            total_amount=total_fee,
            paid_amount=paid_amount,
            payment_status="Paid" if (paid_amount >= total_fee and total_fee > 0) else "Due",
            payment_method="Cash",
            items_json=json.dumps(items),
            source="booking",
            booking_id=booking.booking_id,
        )
        db.add(bill)
    else:
        bill.patient_name = patient_name
        bill.patient_id = patient_id_str
        bill.patient_phone = patient_phone
        bill.bill_type = "Service"
        bill.description = service_name
        bill.doctor = doctor_name
        bill.department = department
        bill.subtotal = subtotal
        bill.tax = tax
        bill.total_amount = total_fee
        bill.source = "booking"
        bill.booking_id = booking.booking_id
        cur_paid = float(bill.paid_amount or 0.0)
        if cur_paid >= (total_fee - 0.01) and total_fee > 0:
            bill.payment_status = "Paid"
            # Keep booking in sync
            booking.payment_status = "Paid"
        elif cur_paid > 0:
            bill.payment_status = "Due"
            # Keep booking in sync — partial payment
            booking.payment_status = "Partial"
        else:
            bill.payment_status = "Due"
            booking.payment_status = "Pending"
        bill.items_json = json.dumps(items)

    return bill



def generate_bill_for_patient(patient: Patient, db: Session) -> Bill:
    """
    Generate or update a bill corresponding to a patient registration / patient booked services.
    """
    inv_num = f"INV-{patient.registration_number}"
    bill = db.query(Bill).filter(Bill.invoice_number == inv_num).first()

    # Check if patient selected specific services during registration
    services_found = []
    if patient.services:
        try:
            parsed = json.loads(patient.services)
            if isinstance(parsed, list):
                for item in parsed:
                    if isinstance(item, int) or (isinstance(item, str) and item.isdigit()):
                        srv = db.query(Service).filter(Service.id == int(item)).first()
                        if srv:
                            services_found.append(srv)
                    elif isinstance(item, str):
                        srv = db.query(Service).filter(Service.name.ilike(f"%{item}%")).first()
                        if srv:
                            services_found.append(srv)
            elif isinstance(parsed, (int, str)):
                if isinstance(parsed, int) or str(parsed).isdigit():
                    srv = db.query(Service).filter(Service.id == int(parsed)).first()
                    if srv:
                        services_found.append(srv)
                else:
                    srv = db.query(Service).filter(Service.name.ilike(f"%{parsed}%")).first()
                    if srv:
                        services_found.append(srv)
        except Exception:
            pass

    # Registered patient should NOT be reflected on billing until they take any services
    if not services_found:
        if bill and float(bill.paid_amount or 0.0) <= 0.0:
            db.delete(bill)
        return None

    items = []
    total_fee = 0.0
    primary_service_name = services_found[0].name
    primary_service_id = services_found[0].id
    department = services_found[0].category or "General Medicine"

    for srv in services_found:
        price = float(srv.price) if srv.price else 500.0
        total_fee += price
        items.append({
            "description": f"{srv.name} (Patient Registration)",
            "category": srv.name,
            "service_name": srv.name,
            "service_id": srv.id,
            "quantity": 1,
            "rate": price,
            "unitPrice": price,
            "amount": price,
            "discount": 0,
        })

    tax_rate = get_hospital_tax_rate(db)
    tax = round(total_fee * (tax_rate / 100.0), 2)
    subtotal = round(total_fee - tax, 2) if total_fee >= tax else total_fee

    patient_full_name = f"{patient.first_name} {patient.last_name or ''}".strip()
    patient_age = str(patient.age) if patient.age else "30"
    patient_gender = patient.gender or "Not Specified"
    patient_phone = patient.phone or ""
    patient_email = patient.email or ""
    patient_address = patient.address or ""
    bill_date = patient.registration_date if patient.registration_date else date.today()

    if not bill:
        bill = Bill(
            invoice_number=inv_num,
            patient_id=patient.registration_number,
            patient_name=patient_full_name,
            patient_age=patient_age,
            patient_gender=patient_gender,
            patient_phone=patient_phone,
            patient_email=patient_email,
            address=patient_address,
            bill_type="Service",
            description=primary_service_name,
            doctor="Hospital Medical Team",
            department=department,
            date=bill_date,
            subtotal=subtotal,
            tax=tax,
            discount=0.0,
            total_amount=total_fee,
            paid_amount=0.0,
            payment_status="Due",
            payment_method="Cash",
            items_json=json.dumps(items),
        )
        db.add(bill)
    else:
        bill.patient_name = patient_full_name
        bill.patient_id = patient.registration_number
        bill.patient_phone = patient_phone
        bill.bill_type = "Service"
        bill.description = primary_service_name
        bill.department = department
        bill.subtotal = subtotal
        bill.tax = tax
        bill.total_amount = total_fee
        cur_paid = float(bill.paid_amount or 0.0)
        if cur_paid >= (total_fee - 0.01) and total_fee > 0:
            bill.payment_status = "Paid"
        else:
            bill.payment_status = "Due"
        bill.items_json = json.dumps(items)

    return bill


def sync_bills_from_patients_and_bookings(db: Session):
    """
    Sync all patients and bookings into bills table idempotently.
    """
    clean_legacy_dummy_bills(db)

    # 1. Sync Bookings
    bookings = db.query(Booking).all()
    for b in bookings:
        generate_bill_for_booking(b, db)

    # 2. Sync Patients
    patients = db.query(Patient).all()
    for p in patients:
        generate_bill_for_patient(p, db)

    db.commit()


def create_manual_bill(data: ManualBillCreate, db: Session) -> Bill:
    """
    Create a manual bill selecting existing patient and service, with optional
    medicines, room charges, doctor appointment charges, other charges, and discount.
    """
    # 1. Look up Patient
    patient = None
    if isinstance(data.patient_id, int) or (isinstance(data.patient_id, str) and str(data.patient_id).isdigit()):
        patient = db.query(Patient).filter(Patient.id == int(data.patient_id)).first()
    if not patient:
        patient = db.query(Patient).filter(Patient.registration_number == str(data.patient_id)).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found in database."
        )

    # 2. Look up Primary Service
    service = db.query(Service).filter(Service.id == data.service_id).first()
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Selected service not found in database."
        )

    service_name = service.name
    department = service.category or "General Medicine"
    service_price = float(service.price or 0.0)
    duration_str = data.duration.strip() if data.duration else "1 Day"

    items = []
    # Primary Service charge item
    items.append({
        "description": f"{service_name} ({duration_str})",
        "category": department or "Service",
        "service_name": service_name,
        "service_id": service.id,
        "quantity": 1,
        "rate": service_price,
        "unitPrice": service_price,
        "amount": service_price,
        "discount": 0,
    })

    service_charge_total = service_price
    medicines_total = 0.0
    room_total = 0.0
    appointment_total = 0.0
    other_total = 0.0

    # 3. Medicine charges (optional & multiple)
    if data.medicines:
        for med in data.medicines:
            med_price = float(med.price or 0.0)
            med_qty = int(med.quantity if med.quantity and med.quantity > 0 else 1)
            med_amount = round(med_qty * med_price, 2)
            medicines_total += med_amount
            items.append({
                "description": f"Medicine: {med.medicine_name}",
                "category": "Pharmacy",
                "service_name": med.medicine_name,
                "service_id": med.medicine_id,
                "quantity": med_qty,
                "rate": med_price,
                "unitPrice": med_price,
                "amount": med_amount,
                "discount": 0,
            })

    # 4. Room Charge (optional)
    if data.room_charge:
        rc = data.room_charge
        days = int(rc.days if rc.days and rc.days > 0 else 1)
        price_per_day = float(rc.price_per_day or 0.0)
        calc_room = round(days * price_per_day, 2)
        room_total += calc_room
        room_desc = f"Room Charge: Room {rc.room_number or ''} ({rc.room_type or rc.ward or 'General'}) - {days} Day(s)"
        items.append({
            "description": room_desc,
            "category": "Room & Bed",
            "service_name": f"Room {rc.room_number or ''}",
            "service_id": rc.room_id,
            "quantity": days,
            "rate": price_per_day,
            "unitPrice": price_per_day,
            "amount": calc_room,
            "discount": 0,
        })

    # 5. Appointment Charge (optional)
    doctor_name = "Hospital Medical Team"
    if data.appointment:
        app = data.appointment
        app_charge = float(app.charge or 0.0)
        appointment_total += app_charge
        doc_label = app.doctor_name or "Consulting Doctor"
        doctor_name = doc_label
        date_label = f" on {app.date}" if app.date else ""
        items.append({
            "description": f"Doctor Appointment: {doc_label}{date_label}",
            "category": "Consultation",
            "service_name": doc_label,
            "service_id": app.doctor_id,
            "quantity": 1,
            "rate": app_charge,
            "unitPrice": app_charge,
            "amount": app_charge,
            "discount": 0,
        })

    # 6. Other Charges (optional)
    if data.other_charges:
        oth = data.other_charges
        oth_amount = float(oth.amount or 0.0)
        other_total += oth_amount
        oth_desc = oth.description.strip() if oth.description and oth.description.strip() else "Other Hospital Charges"
        items.append({
            "description": f"Other: {oth_desc}",
            "category": "Miscellaneous",
            "service_name": oth_desc,
            "service_id": None,
            "quantity": 1,
            "rate": oth_amount,
            "unitPrice": oth_amount,
            "amount": oth_amount,
            "discount": 0,
        })

    # Calculations:
    # Service Charge + Medicine Charges + Room Charges + Appointment Charges + Other Charges - Discount = Final Total
    subtotal = round(service_charge_total + medicines_total + room_total + appointment_total + other_total, 2)
    discount = round(max(0.0, float(data.discount or 0.0)), 2)
    taxable_amount = max(0.0, subtotal - discount)
    tax_rate = float(data.tax_rate if data.tax_rate is not None and data.tax_rate >= 0 else 5.0)
    tax = round(taxable_amount * (tax_rate / 100.0), 2)
    total_amount = round(taxable_amount + tax, 2)

    # Payment Status & Paid Amount
    raw_status = (data.payment_status or "Unpaid").strip().lower()
    if raw_status == "paid":
        paid_amount = total_amount
        final_payment_status = "Paid"
    elif raw_status in ["partially paid", "partial"]:
        paid_amount = round(min(total_amount, max(0.0, float(data.paid_amount or 0.0))), 2)
        final_payment_status = "Paid" if paid_amount >= (total_amount - 0.01) and total_amount > 0 else "Due"
    else:  # unpaid / due
        paid_amount = 0.0
        final_payment_status = "Due"

    # Patient demographics
    patient_full_name = f"{patient.first_name} {patient.last_name or ''}".strip()
    patient_age = str(patient.age) if patient.age else "30"
    patient_gender = patient.gender or "Not Specified"
    patient_phone = patient.phone or ""
    patient_email = patient.email or ""
    patient_address = patient.address or ""
    bill_date = date.today()

    # Generate unique invoice number: INV-MAN-YYYY-XXXXX
    year_str = str(bill_date.year)
    latest_manual = db.query(Bill).filter(Bill.invoice_number.like(f"INV-MAN-{year_str}-%")).order_by(Bill.id.desc()).first()
    next_seq = 1
    if latest_manual and latest_manual.invoice_number:
        try:
            parts = latest_manual.invoice_number.split("-")
            if len(parts) >= 4 and parts[-1].isdigit():
                next_seq = int(parts[-1]) + 1
        except Exception:
            next_seq = 1
    inv_num = f"INV-MAN-{year_str}-{next_seq:05d}"

    while db.query(Bill).filter(Bill.invoice_number == inv_num).first():
        next_seq += 1
        inv_num = f"INV-MAN-{year_str}-{next_seq:05d}"

    bill = Bill(
        invoice_number=inv_num,
        patient_id=patient.registration_number,
        patient_name=patient_full_name,
        patient_age=patient_age,
        patient_gender=patient_gender,
        patient_phone=patient_phone,
        patient_email=patient_email,
        address=patient_address,
        bill_type="Service",
        description=f"{service_name} (Manual Bill)",
        doctor=doctor_name,
        department=department,
        date=bill_date,
        subtotal=subtotal,
        tax=tax,
        discount=discount,
        total_amount=total_amount,
        paid_amount=paid_amount,
        payment_status=final_payment_status,
        payment_method=data.payment_method or "Cash",
        items_json=json.dumps(items),
        source="manual",
        booking_id=None,
    )
    db.add(bill)
    db.commit()
    db.refresh(bill)
    return bill

