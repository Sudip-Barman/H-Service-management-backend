import json
from datetime import date, datetime
from app.database import SessionLocal
from app.models.admission import Admission
from app.models.attendance import Attendance
from app.models.billing import Bill
from app.models.blood_bank import BloodStock
from app.models.doctor import Doctor
from app.models.emergency import EmergencyPatient
from app.models.feedback import Feedback
from app.models.followup import FollowUp
from app.models.inventory import InventoryItem
from app.models.medicine import Medicine
from app.models.notification import Notification
from app.models.nurse import Nurse
from app.models.patient import Patient
from app.models.request import HospitalRequest
from app.models.room_bed import Bed, Room
from app.models.schedule import Schedule
from app.models.service import Service
from app.models.shift import StaffShift
from app.models.staff import Staff
from app.models.user import User
from app.core.security import hash_password


def seed():
    db = SessionLocal()
    try:
        # 1. Staff & Doctors & Nurses
        if db.query(Staff).count() == 0:
            staff_members = [
                Staff(name="Dr. Arindam Sen", role="Doctor", gender="Male", phone="+91 98765 43210", email="arindam.sen@hospital.com", qualification="MBBS, MD, DM", experience="15 Years", status="Active"),
                Staff(name="Dr. Moumita Roy", role="Doctor", gender="Female", phone="+91 98765 43211", email="moumita.roy@hospital.com", qualification="MBBS, MD, DM", experience="11 Years", status="Active"),
                Staff(name="Dr. Sourav Mukherjee", role="Doctor", gender="Male", phone="+91 98765 43212", email="sourav.m@hospital.com", qualification="MS, MCh (Ortho)", experience="14 Years", status="Active"),
                Staff(name="Dr. Ananya Das", role="Doctor", gender="Female", phone="+91 98765 43213", email="ananya.das@hospital.com", qualification="MBBS, MD (Derma)", experience="9 Years", status="Active"),
                Staff(name="Priyanka Das", role="Nurse", gender="Female", phone="+91 98765 43220", email="priyanka.das@hospital.com", qualification="B.Sc Nursing", experience="6 Years", status="Active"),
                Staff(name="Moumita Ghosh", role="Nurse", gender="Female", phone="+91 98301 23456", email="moumita.ghosh@hospital.com", qualification="B.Sc Nursing", experience="8 Years", status="Active"),
                Staff(name="Suman Roy", role="Nurse", gender="Male", phone="+91 98765 12002", email="suman.roy@carecore.com", qualification="GNM Nursing", experience="7 Years", status="Active"),
                Staff(name="Anita Roy", role="Caregiver", gender="Female", phone="+91 98765 12003", email="anita.roy@carecore.com", qualification="Caregiver Training", experience="5 Years", status="Active"),
                Staff(name="Amit Sharma", role="Receptionist", gender="Male", phone="+91 98765 12004", email="amit.sharma@hospital.com", qualification="Graduate", experience="4 Years", status="Active"),
                Staff(name="Rahul Ghosh", role="Technician", gender="Male", phone="+91 98765 12005", email="rahul.ghosh@hospital.com", qualification="DMLT", experience="5 Years", status="Active"),
            ]
            db.add_all(staff_members)
            db.commit()

        # 2. Doctors
        if db.query(Doctor).count() == 0:
            doctors = [
                Doctor(
                    registration_number="REG-DOC-001",
                    first_name="Arindam",
                    last_name="Sen",
                    gender="Male",
                    phone="+91 9876543210",
                    email="arindam.sen@hospital.com",
                    address="Kolkata, West Bengal",
                    specialization="Cardiology",
                    department="Cardiology",
                    qualification="MBBS, MD, DM",
                    experience_years=15,
                    consultation_fee=1200.0,
                    license_number="WB-MC-10001",
                    available_status="Available",
                    status="Active"
                ),
                Doctor(
                    registration_number="REG-DOC-002",
                    first_name="Moumita",
                    last_name="Roy",
                    gender="Female",
                    phone="+91 9876543211",
                    email="moumita.roy@hospital.com",
                    address="Salt Lake, Kolkata",
                    specialization="Neurology",
                    department="Neurology",
                    qualification="MBBS, MD, DM",
                    experience_years=11,
                    consultation_fee=1500.0,
                    license_number="WB-MC-10002",
                    available_status="Available",
                    status="Active"
                ),
                Doctor(
                    registration_number="REG-DOC-003",
                    first_name="Sourav",
                    last_name="Mukherjee",
                    gender="Male",
                    phone="+91 9876543212",
                    email="sourav.m@hospital.com",
                    address="New Town, Kolkata",
                    specialization="Orthopedics",
                    department="Orthopedics",
                    qualification="MBBS, MS, MCh",
                    experience_years=14,
                    consultation_fee=1300.0,
                    license_number="WB-MC-10003",
                    available_status="Available",
                    status="Active"
                ),
                Doctor(
                    registration_number="REG-DOC-004",
                    first_name="Ananya",
                    last_name="Das",
                    gender="Female",
                    phone="+91 9876543213",
                    email="ananya.das@hospital.com",
                    address="Ballygunge, Kolkata",
                    specialization="Dermatology",
                    department="Dermatology",
                    qualification="MBBS, MD",
                    experience_years=9,
                    consultation_fee=1000.0,
                    license_number="WB-MC-10004",
                    available_status="Available",
                    status="Active"
                ),
            ]
            db.add_all(doctors)
            db.commit()

        # 3. Nurses
        if db.query(Nurse).count() == 0:
            nurses = [
                Nurse(
                    nurse_id=1,
                    staff_id=5,
                    registration_number="REG-NUR-001",
                    first_name="Priyanka",
                    last_name="Das",
                    gender="Female",
                    phone="9876543210",
                    email="priyanka.das@hospital.com",
                    address="Kolkata, West Bengal",
                    qualification="B.Sc Nursing",
                    department="Emergency",
                    ward="Emergency Ward",
                    experience_years=6,
                    license_number="WB-NUR-1001",
                    shift_type="Morning",
                    status="Active"
                ),
                Nurse(
                    nurse_id=2,
                    staff_id=6,
                    registration_number="REG-NUR-002",
                    first_name="Moumita",
                    last_name="Ghosh",
                    gender="Female",
                    phone="9830123456",
                    email="moumita.ghosh@hospital.com",
                    address="Howrah, West Bengal",
                    qualification="B.Sc Nursing",
                    department="ICU",
                    ward="ICU",
                    experience_years=8,
                    license_number="WB-NUR-1002",
                    shift_type="Night",
                    status="Active"
                ),
                Nurse(
                    nurse_id=3,
                    staff_id=7,
                    registration_number="REG-NUR-003",
                    first_name="Suman",
                    last_name="Roy",
                    gender="Male",
                    phone="9876512002",
                    email="suman.roy@carecore.com",
                    address="Kolkata, West Bengal",
                    qualification="GNM Nursing",
                    department="General Ward",
                    ward="General Ward",
                    experience_years=7,
                    license_number="WB-NUR-1003",
                    shift_type="Morning",
                    status="Active"
                )
            ]
            db.add_all(nurses)
            db.commit()

        # 4. Rooms & Beds
        if db.query(Room).count() == 0:
            rooms_data = [
                ("101", "General Ward", "General", "1st Floor", "General Medicine", 500.0, 4),
                ("102", "General Ward", "General", "1st Floor", "General Medicine", 500.0, 4),
                ("201", "ICU", "ICU", "2nd Floor", "Critical Care", 2500.0, 4),
                ("301", "Cabin", "Private", "3rd Floor", "Executive Care", 1800.0, 2),
            ]
            for r_num, ward, r_type, floor, dept, charge, bed_count in rooms_data:
                room = Room(
                    room_number=r_num,
                    ward=ward,
                    room_type=r_type,
                    floor=floor,
                    department=dept,
                    daily_charge=charge,
                    status="Active"
                )
                db.add(room)
                db.flush()

                for b_idx in range(1, bed_count + 1):
                    bed = Bed(
                        room_id=room.id,
                        bed_number=f"Bed {b_idx}",
                        status="Available",
                        daily_charge=charge
                    )
                    db.add(bed)
            db.commit()

        # 5. Medicines
        if db.query(Medicine).count() == 0:
            medicines = [
                Medicine(medicine_code="MED001", medicine_name="Paracetamol 500mg", generic_name="Paracetamol", medicine_type="Tablet", category="Pain Relief", manufacturer="Cipla", batch_number="PCM001", dosage="500mg", unit="Tablet", quantity=250, reorder_level=50, purchase_price=1.5, selling_price=2.0, storage_location="Rack A-01", prescription_required=False, status="Available"),
                Medicine(medicine_code="MED002", medicine_name="Amoxicillin 500mg", generic_name="Amoxicillin", medicine_type="Capsule", category="Antibiotic", manufacturer="Sun Pharma", batch_number="AMX002", dosage="500mg", unit="Capsule", quantity=120, reorder_level=30, purchase_price=6.0, selling_price=8.0, storage_location="Rack A-02", prescription_required=True, status="Available"),
                Medicine(medicine_code="MED003", medicine_name="Ibuprofen 400mg", generic_name="Ibuprofen", medicine_type="Tablet", category="Pain Relief", manufacturer="Abbott", batch_number="IBU003", dosage="400mg", unit="Tablet", quantity=180, reorder_level=40, purchase_price=2.0, selling_price=3.0, storage_location="Rack A-03", prescription_required=False, status="Available"),
                Medicine(medicine_code="MED004", medicine_name="Cough Syrup 100ml", generic_name="Dextromethorphan", medicine_type="Syrup", category="Respiratory", manufacturer="Dabur", batch_number="CPH004", dosage="100ml", unit="Bottle", quantity=45, reorder_level=20, purchase_price=45.0, selling_price=60.0, storage_location="Rack B-01", prescription_required=False, status="Available"),
                Medicine(medicine_code="MED005", medicine_name="Insulin Regular 100IU", generic_name="Insulin", medicine_type="Injection", category="Diabetes", manufacturer="Novo Nordisk", batch_number="INS005", dosage="100IU/ml", unit="Vial", quantity=15, reorder_level=20, purchase_price=150.0, selling_price=190.0, storage_location="Fridge 1", prescription_required=True, status="Low Stock"),
            ]
            db.add_all(medicines)
            db.commit()

        # 6. Blood Stocks
        if db.query(BloodStock).count() == 0:
            blood_data = [
                ("A+", "Whole Blood", 24, 10, 12, "Available", "Blood Bank - A"),
                ("A-", "Whole Blood", 6, 8, 4, "Low Stock", "Blood Bank - A"),
                ("B+", "Whole Blood", 32, 12, 18, "Available", "Blood Bank - B"),
                ("B-", "Platelets", 5, 8, 3, "Low Stock", "Blood Bank - B"),
                ("AB+", "Plasma", 18, 10, 8, "Available", "Blood Bank - A"),
                ("AB-", "Whole Blood", 4, 6, 2, "Low Stock", "Blood Bank - A"),
                ("O+", "Whole Blood", 40, 15, 25, "Available", "Blood Bank - A"),
                ("O-", "Whole Blood", 3, 10, 2, "Critical", "Blood Bank - B"),
            ]
            for bg, comp, units, min_s, donors, stat, loc in blood_data:
                db.add(BloodStock(blood_group=bg, component=comp, units=units, min_stock=min_s, donor_count=donors, status=stat, location=loc))
            db.commit()

        # 7. Inventory Items
        if db.query(InventoryItem).count() == 0:
            inventory_items = [
                InventoryItem(code="INV-001", name="Surgical Gloves", category="Surgical Items", item_type="Disposable", unit="Box", quantity=500, minimum=100, maximum=1000, price=250.0, supplier="MedSupply India", location="Store Room A", status="Available"),
                InventoryItem(code="INV-002", name="Disposable Syringe 5ml", category="Consumables", item_type="Disposable", unit="Box", quantity=350, minimum=80, maximum=800, price=120.0, supplier="Healthcare Equip Co", location="Store Room A", status="Available"),
                InventoryItem(code="INV-003", name="N95 Face Masks", category="Safety Gear", item_type="PPE", unit="Box", quantity=200, minimum=50, maximum=500, price=300.0, supplier="SafetyMed Ltd", location="Store Room B", status="Available"),
                InventoryItem(code="INV-004", name="IV Infusion Set", category="Consumables", item_type="Disposable", unit="Pack", quantity=40, minimum=50, maximum=300, price=45.0, supplier="MedSupply India", location="Store Room A", status="Low Stock"),
                InventoryItem(code="INV-005", name="Digital Thermometer", category="Equipment", item_type="Reusable", unit="Piece", quantity=25, minimum=10, maximum=50, price=450.0, supplier="Omron Healthcare", location="Store Room C", status="Available"),
            ]
            db.add_all(inventory_items)
            db.commit()

        # 8. Schedules
        if db.query(Schedule).count() == 0:
            today = date.today()
            schedules = [
                Schedule(doctor_id=1, doctor_name="Dr. Arindam Sen", department="Cardiology", date=today, start_time="09:00", end_time="13:00", location="OPD Room 201", type="Consultation", status="Available"),
                Schedule(doctor_id=2, doctor_name="Dr. Moumita Roy", department="Neurology", date=today, start_time="10:00", end_time="14:00", location="OPD Room 205", type="Consultation", status="Available"),
                Schedule(doctor_id=3, doctor_name="Dr. Sourav Mukherjee", department="Orthopedics", date=today, start_time="08:00", end_time="12:00", location="OT 2", type="Surgery", status="Booked"),
                Schedule(doctor_id=4, doctor_name="Dr. Ananya Das", department="Dermatology", date=today, start_time="14:00", end_time="18:00", location="OPD Room 108", type="Consultation", status="Available"),
            ]
            db.add_all(schedules)
            db.commit()

        # 9. Shifts
        if db.query(StaffShift).count() == 0:
            today = date.today()
            shifts = [
                StaffShift(shift_code="SH-1001", staff_id=9, staff_name="Amit Sharma", employee_id="EMP-1009", department="Reception", date=today, shift="Morning", start_time="08:00", end_time="16:00", location="Main Reception", status="Scheduled", notes="Front desk duty"),
                StaffShift(shift_code="SH-1002", staff_id=5, staff_name="Priyanka Das", employee_id="EMP-1005", department="Nursing", date=today, shift="Morning", start_time="08:00", end_time="16:00", location="Ward A", status="Scheduled", notes="General ward duty"),
                StaffShift(shift_code="SH-1003", staff_id=10, staff_name="Rahul Ghosh", employee_id="EMP-1010", department="Laboratory", date=today, shift="Evening", start_time="16:00", end_time="00:00", location="Lab 01", status="Scheduled", notes="Pathology laboratory"),
            ]
            db.add_all(shifts)
            db.commit()

        # 10. Attendance
        if db.query(Attendance).count() == 0:
            today = date.today()
            att_records = [
                Attendance(staff_id=1, employee_id="EMP-1001", staff_name="Dr. Arindam Sen", role="Doctor", department="Cardiology", date=today, shift="09:00 AM - 05:00 PM", check_in="08:55 AM", status="Present"),
                Attendance(staff_id=2, employee_id="EMP-1002", staff_name="Dr. Moumita Roy", role="Doctor", department="Neurology", date=today, shift="09:00 AM - 05:00 PM", check_in="09:10 AM", status="Present"),
                Attendance(staff_id=5, employee_id="EMP-1005", staff_name="Priyanka Das", role="Nurse", department="Nursing", date=today, shift="08:00 AM - 04:00 PM", check_in="07:50 AM", status="Present"),
                Attendance(staff_id=9, employee_id="EMP-1009", staff_name="Amit Sharma", role="Receptionist", department="Reception", date=today, shift="08:00 AM - 04:00 PM", check_in="08:00 AM", status="Present"),
            ]
            db.add_all(att_records)
            db.commit()

        # 11. Emergency Patients
        if db.query(EmergencyPatient).count() == 0:
            er_patients = [
                EmergencyPatient(emergency_code="ER-24081", name="Arjun Mehta", age="46", gender="Male", blood_group="B+", phone="+91 98765 22011", emergency_contact="Neha Mehta", emergency_phone="+91 98765 22012", arrival_time="Today, 09:42 AM", triage="Critical", status="Under Treatment", condition_summary="Chest pain and breathing difficulty", symptoms="Severe chest pain, shortness of breath", assigned_doctor="Dr. Arindam Sen", department="Emergency Medicine", room="Resus Bay 01", allergies="Penicillin", notes="ECG completed. Cardiology review requested."),
                EmergencyPatient(emergency_code="ER-24080", name="Maya Roy", age="29", gender="Female", blood_group="O+", phone="+91 91234 66890", emergency_contact="Sourav Roy", emergency_phone="+91 91234 66891", arrival_time="Today, 10:05 AM", triage="Urgent", status="Awaiting Doctor", condition_summary="Abdominal pain and vomiting", symptoms="Right-sided abdominal pain, fever", assigned_doctor="Dr. Moumita Roy", department="Emergency Medicine", room="Exam Room 04", allergies="None", notes="Blood tests pending."),
            ]
            db.add_all(er_patients)
            db.commit()

        # 12. Bills
        if db.query(Bill).count() == 0:
            today = date.today()
            items_1 = json.dumps([
                {"description": "Specialist Doctor Consultation", "category": "Consultation", "quantity": 1, "unitPrice": 1200, "amount": 1200},
                {"description": "ECG Diagnostic Test", "category": "Diagnostics", "quantity": 1, "unitPrice": 500, "amount": 500}
            ])
            bills = [
                Bill(invoice_number="INV-2026-001", patient_id="PAT-0001", patient_name="Rahul Sharma", patient_age="42", patient_gender="Male", patient_phone="+91 98765 12345", address="Kolkata, West Bengal", bill_type="Patient", description="General Consultation", doctor="Dr. Arindam Sen", department="Cardiology", date=today, subtotal=1700.0, tax=85.0, discount=0.0, total_amount=1785.0, paid_amount=1785.0, payment_status="Paid", payment_method="UPI", items_json=items_1),
            ]
            db.add_all(bills)
            db.commit()

        # 13. Follow-ups
        if db.query(FollowUp).count() == 0:
            today = date.today()
            fus = [
                FollowUp(follow_up_code="FU-1001", name="Ananya Sharma", phone="+91 98765 43210", email="ananya.sharma@example.com", patient_id="PAT-0001", relation="Self", source="Phone Call", followup_type="Admission Enquiry", query="Wants information about ICU admission.", priority="High", follow_up_date=today, assigned_to="Reception", notes="Family is looking for ICU admission details.", next_action="Confirm bed availability and call back.", status="Follow-up Required"),
                FollowUp(follow_up_code="FU-1002", name="Rahul Das", phone="+91 98321 45678", email="rahul.das@example.com", patient_id="PAT-0002", relation="Self", source="Appointment", followup_type="Medical Follow Up", query="Post-treatment review with doctor.", priority="Medium", follow_up_date=today, assigned_to="Dr. Arindam Sen", notes="Patient needs review after previous treatment.", next_action="Confirm appointment.", status="Scheduled"),
            ]
            db.add_all(fus)
            db.commit()

        # 14. Hospital Requests
        if db.query(HospitalRequest).count() == 0:
            today = date.today()
            reqs = [
                HospitalRequest(request_code="REQ-1001", request_type="Lab Test", item="Complete Blood Count", requested_for="Rahul Sharma", patient_id="PAT-0001", requested_by="Dr. Arindam Sen", department="Laboratory", priority="Urgent", status="Pending", date=today, required_date=today, description="CBC required for immediate diagnosis."),
                HospitalRequest(request_code="REQ-1002", request_type="Medicine", item="Paracetamol 500mg", requested_for="Maya Roy", patient_id="PAT-0002", requested_by="Nurse Priyanka", department="Pharmacy", priority="Normal", status="Approved", date=today, required_date=today, description="Medicine required for inpatient treatment."),
            ]
            db.add_all(reqs)
            db.commit()

        # 15. Notifications
        if db.query(Notification).count() == 0:
            notifs = [
                Notification(title="Blood Bank Stock Alert", message="O negative blood stock is below the emergency reserve level.", type="Blood Bank", priority="Urgent", department="Blood Bank", recipient="All Clinical Staff", read=False),
                Notification(title="Medicine Expiry Reminder", message="Insulin Regular 100IU batches need reordering.", type="Pharmacy", priority="High", department="Pharmacy", recipient="Pharmacy Team", read=False),
                Notification(title="Emergency Department Roster Updated", message="The emergency department staff schedule has been updated.", type="Staff", priority="Normal", department="Emergency", recipient="Emergency Team", read=True),
            ]
            db.add_all(notifs)
            db.commit()

        # 16. Feedback
        if db.query(Feedback).count() == 0:
            today_str = date.today().strftime("%d %b %Y")
            fbs = [
                Feedback(feedback_code="FB-2048", patient="Priya Sharma", email="priya.sharma@example.com", service="Outpatient consultation", rating=5, status="New", date=today_str, comment="The reception team was kind and the doctor explained every step clearly."),
                Feedback(feedback_code="FB-2047", patient="Rahul Das", email="rahul.das@example.com", service="Elder care support", rating=4, status="Reviewed", date=today_str, comment="Very helpful care team. The follow-up call was thoughtful."),
            ]
            db.add_all(fbs)
            db.commit()

        print("Seeding completed successfully!")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
