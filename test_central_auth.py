"""
Comprehensive Automated Test Suite for Centralized Authentication System.
Uses Python standard library urllib to test the running FastAPI backend directly.
Tests:
1. Admin Login & Authorization
2. Doctor Login, First-time Password Change & Portal Access
3. Nurse Login, First-time Password Change & Portal Access
4. Staff Login, First-time Password Change & Portal Access
5. Invalid Credentials (401)
6. Inactive Account (403)
7. Role Tampering & Privilege Escalation Prevention (403)
8. GET /api/auth/me endpoint verification for all roles
"""

import json
import urllib.request
import urllib.error
from app.database import SessionLocal
from app.models.user import User
from app.models.doctor import Doctor
from app.models.nurse import Nurse
from app.models.staff import Staff
from app.core.security import hash_password, create_access_token

BASE_URL = "http://127.0.0.1:8000"


class APIClient:
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url

    def request(self, method, path, data=None, token=None):
        url = f"{self.base_url}{path}"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"

        encoded_data = json.dumps(data).encode("utf-8") if data is not None else None
        req = urllib.request.Request(url, data=encoded_data, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req) as resp:
                status = resp.status
                body = resp.read().decode("utf-8")
                return status, json.loads(body) if body else None
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8")
            try:
                parsed = json.loads(body)
            except Exception:
                parsed = body
            return e.code, parsed

    def get(self, path, token=None):
        return self.request("GET", path, token=token)

    def post(self, path, data, token=None):
        return self.request("POST", path, data=data, token=token)


client = APIClient()


def run_tests():
    print("=" * 70)
    print("RUNNING CENTRALIZED AUTHENTICATION TEST SUITE VIA HTTP")
    print("=" * 70)

    db = SessionLocal()
    try:
        # Prepare test accounts
        admin = db.query(User).filter(User.role == "admin").first()
        assert admin is not None, "Admin user must exist"
        admin.password_hash = hash_password("Admin@123456")
        admin.is_active = True
        db.commit()

        doc_user = db.query(User).filter(User.username == "dr_arindam").first()
        if not doc_user:
            doc_user = db.query(User).filter(User.role == "doctor").first()
        if doc_user:
            doc_user.password_hash = hash_password("TempPass@123")
            doc_user.must_change_password = True
            doc_user.is_active = True
            doc_rec = db.query(Doctor).filter(Doctor.user_id == doc_user.id).first()
            if not doc_rec:
                doc_rec = Doctor(
                    user_id=doc_user.id,
                    registration_number="REG-DOC-TEST",
                    first_name=doc_user.name.split()[0] if doc_user.name else "Doctor",
                    last_name="Test",
                    phone="9876543210",
                    email=doc_user.email,
                    specialization="Cardiology",
                    department="Cardiology"
                )
                db.add(doc_rec)
            db.commit()

        nurse_user = db.query(User).filter(User.username == "nurse_moumita").first()
        if not nurse_user:
            nurse_user = db.query(User).filter(User.role == "nurse").first()
        if nurse_user:
            nurse_user.password_hash = hash_password("TempPass@123")
            nurse_user.must_change_password = True
            nurse_user.is_active = True
            nurse_rec = db.query(Nurse).filter(Nurse.user_id == nurse_user.id).first()
            if not nurse_rec:
                nurse_rec = Nurse(
                    user_id=nurse_user.id,
                    staff_id=101,
                    registration_number="REG-NUR-TEST",
                    first_name=nurse_user.name.split()[0] if nurse_user.name else "Nurse",
                    last_name="Test",
                    phone="9876543211",
                    email=nurse_user.email,
                    department="ICU"
                )
                db.add(nurse_rec)
            db.commit()

        staff_user = db.query(User).filter(User.username == "staff_amit_sharma").first()
        if not staff_user:
            staff_user = db.query(User).filter(User.role == "staff").first()
        if staff_user:
            staff_user.password_hash = hash_password("TempPass@123")
            staff_user.must_change_password = True
            staff_user.is_active = True
            staff_rec = db.query(Staff).filter(Staff.user_id == staff_user.id).first()
            if not staff_rec:
                staff_rec = Staff(
                    user_id=staff_user.id,
                    name=staff_user.name or "Staff Member",
                    role="Receptionist",
                    gender="Male",
                    phone="9876543212",
                    email=staff_user.email,
                    qualification="B.Com"
                )
                db.add(staff_rec)
            db.commit()

        # -------------------------------------------------------------
        # TEST 1: Admin Login & Authorization
        # -------------------------------------------------------------
        print("\n[TEST 1] Admin Login & Authorization")
        status_code, data = client.post("/api/auth/login", {
            "email": admin.email,
            "password": "Admin@123456",
            "role": "admin"
        })
        assert status_code == 200, f"Admin login failed: {data}"
        assert data["user"]["role"] == "admin"
        assert data["user"]["must_change_password"] is False
        admin_token = data["access_token"]
        print("  -> Admin login successful through Admin portal option, JWT token received, role='admin'")

        # Admin attempting to log in under Staff portal option -> rejected
        status_code, res_admin_staff = client.post("/api/auth/login", {
            "email": admin.email,
            "password": "Admin@123456",
            "role": "staff"
        })
        assert status_code == 403, f"Admin under staff should be 403, got {status_code}"
        print("  -> Admin login attempt under Staff portal option: REJECTED (403 Forbidden)")

        status_code, res_admin = client.get("/api/test/admin", token=admin_token)
        assert status_code == 200, f"Admin route failed: {res_admin}"
        print("  -> Admin access to /api/test/admin: GRANTED (200 OK)")

        status_code, res_doc = client.get("/api/test/doctor", token=admin_token)
        assert status_code == 403, f"Admin should not access doctor route: {res_doc}"
        print("  -> Admin access to /api/test/doctor: RESTRICTED (403 Forbidden)")

        status_code, res_me = client.get("/api/auth/me", token=admin_token)
        assert status_code == 200
        assert res_me["role"] == "admin"
        assert res_me["profile"] is None
        print("  -> Admin /api/auth/me returns valid admin data with profile=None")

        # -------------------------------------------------------------
        # TEST 2: Doctor Login, Temporary Password & Permanent Password Flow
        # -------------------------------------------------------------
        # -------------------------------------------------------------
        # TEST 2: Doctor Login, Temporary Password & Permanent Password Flow
        # -------------------------------------------------------------
        print("\n[TEST 2] Doctor Login, Temporary Password & Permanent Password Flow")
        # Doctor attempting to log in via Admin portal option -> rejected
        status_code, res_doc_as_admin = client.post("/api/auth/login", {
            "email": doc_user.username,
            "password": "TempPass@123",
            "role": "admin"
        })
        assert status_code == 403, f"Doctor should be rejected from Admin option, got {status_code}"
        print("  -> Doctor login attempt under Admin portal option: REJECTED (403 Forbidden)")

        # Doctor logging in via Staff portal option -> successful, role='doctor' preserved
        status_code, data = client.post("/api/auth/login", {
            "email": doc_user.username,
            "password": "TempPass@123",
            "role": "staff"
        })
        assert status_code == 200, f"Doctor temp login failed: {data}"
        assert data["user"]["role"] == "doctor", f"Expected role='doctor', got {data['user']['role']}"
        assert data["user"]["must_change_password"] is True
        assert data["user"]["profile"] is not None
        assert "registration_number" in data["user"]["profile"]
        doc_token = data["access_token"]
        print(f"  -> Doctor login via Staff portal option successful, role='doctor' preserved, must_change_password=True")
        print(f"  -> Attached profile: {data['user']['profile']['name']} ({data['user']['profile']['specialization']})")

        status_code, _ = client.get("/api/test/doctor", token=doc_token)
        assert status_code == 200
        print("  -> Doctor access to /api/test/doctor: GRANTED (200 OK)")

        status_code, _ = client.get("/api/test/admin", token=doc_token)
        assert status_code == 403
        print("  -> Doctor access to /api/test/admin: RESTRICTED (403 Forbidden)")

        # Doctor changes password
        status_code, res_change = client.post("/api/auth/change-password", {
            "current_password": "TempPass@123",
            "new_password": "PermanentDocPass@2026",
            "confirm_password": "PermanentDocPass@2026"
        }, token=doc_token)
        assert status_code == 200, f"Password change failed: {res_change}"
        assert res_change["must_change_password"] is False
        print("  -> Doctor successfully changed temporary password to permanent")

        status_code, res_perm = client.post("/api/auth/login", {
            "email": doc_user.username,
            "password": "PermanentDocPass@2026",
            "role": "staff"
        })
        assert status_code == 200
        assert res_perm["user"]["must_change_password"] is False
        print("  -> Doctor permanent login verified via Staff portal option, must_change_password=False")

        # -------------------------------------------------------------
        # TEST 3: Nurse Login, Temporary Password & Permanent Password Flow
        # -------------------------------------------------------------
        print("\n[TEST 3] Nurse Login, Temporary Password & Permanent Password Flow")
        status_code, res_nurse_admin = client.post("/api/auth/login", {
            "email": nurse_user.username,
            "password": "TempPass@123",
            "role": "admin"
        })
        assert status_code == 403
        print("  -> Nurse login attempt under Admin portal option: REJECTED (403 Forbidden)")

        status_code, data = client.post("/api/auth/login", {
            "email": nurse_user.username,
            "password": "TempPass@123",
            "role": "staff"
        })
        assert status_code == 200, f"Nurse login failed: {data}"
        assert data["user"]["role"] == "nurse", f"Expected role='nurse', got {data['user']['role']}"
        assert data["user"]["must_change_password"] is True
        assert data["user"]["profile"] is not None
        nurse_token = data["access_token"]
        print("  -> Nurse login via Staff portal option successful, role='nurse' preserved, must_change_password=True")

        status_code, _ = client.get("/api/test/nurse", token=nurse_token)
        assert status_code == 200
        print("  -> Nurse access to /api/test/nurse: GRANTED (200 OK)")

        status_code, _ = client.get("/api/test/admin", token=nurse_token)
        assert status_code == 403
        print("  -> Nurse access to /api/test/admin: RESTRICTED (403 Forbidden)")

        status_code, res_change = client.post("/api/auth/change-password", {
            "current_password": "TempPass@123",
            "new_password": "PermanentNursePass@2026",
            "confirm_password": "PermanentNursePass@2026"
        }, token=nurse_token)
        assert status_code == 200
        assert res_change["must_change_password"] is False
        print("  -> Nurse successfully set permanent password")

        # -------------------------------------------------------------
        # TEST 4: Staff Login, Temporary Password & Permanent Password Flow
        # -------------------------------------------------------------
        print("\n[TEST 4] Staff Login, Temporary Password & Permanent Password Flow")
        status_code, res_staff_admin = client.post("/api/auth/login", {
            "email": staff_user.username,
            "password": "TempPass@123",
            "role": "admin"
        })
        assert status_code == 403
        print("  -> Staff login attempt under Admin portal option: REJECTED (403 Forbidden)")

        status_code, data = client.post("/api/auth/login", {
            "email": staff_user.username,
            "password": "TempPass@123",
            "role": "staff"
        })
        assert status_code == 200, f"Staff login failed: {data}"
        assert data["user"]["role"] == "staff"
        assert data["user"]["must_change_password"] is True
        staff_token = data["access_token"]
        print("  -> Staff login via Staff portal option successful, role='staff' preserved, must_change_password=True")

        status_code, _ = client.get("/api/test/staff", token=staff_token)
        assert status_code == 200
        print("  -> Staff access to /api/test/staff: GRANTED (200 OK)")

        status_code, _ = client.get("/api/test/admin", token=staff_token)
        assert status_code == 403
        print("  -> Staff access to /api/test/admin: RESTRICTED (403 Forbidden)")

        status_code, res_change = client.post("/api/auth/change-password", {
            "current_password": "TempPass@123",
            "new_password": "PermanentStaffPass@2026",
            "confirm_password": "PermanentStaffPass@2026"
        }, token=staff_token)
        assert status_code == 200
        assert res_change["must_change_password"] is False
        print("  -> Staff successfully set permanent password")

        # -------------------------------------------------------------
        # TEST 5: Invalid Credentials Test
        # -------------------------------------------------------------
        print("\n[TEST 5] Invalid Credentials Test")
        status_code, _ = client.post("/api/auth/login", {
            "email": admin.email,
            "password": "WrongPassword!999"
        })
        assert status_code == 401
        print("  -> Wrong password rejected with 401 Unauthorized [PASSED]")

        status_code, _ = client.post("/api/auth/login", {
            "email": "nonexistent_user@hospital.com",
            "password": "SomePassword"
        })
        assert status_code == 401
        print("  -> Non-existent user rejected with 401 Unauthorized [PASSED]")

        # -------------------------------------------------------------
        # TEST 6: Inactive Account Test
        # -------------------------------------------------------------
        print("\n[TEST 6] Inactive Account Test")
        staff_user.is_active = False
        db.commit()
        status_code, res_inactive = client.post("/api/auth/login", {
            "email": staff_user.username,
            "password": "PermanentStaffPass@2026"
        })
        assert status_code == 403, f"Expected 403, got {status_code}"
        print("  -> Inactive account login rejected with 403 Forbidden [PASSED]")
        staff_user.is_active = True
        db.commit()

        # -------------------------------------------------------------
        # TEST 7: Role Tampering / Unauthorized Access Test
        # -------------------------------------------------------------
        print("\n[TEST 7] Role Tampering / Unauthorized Access Test")
        fake_token = create_access_token({"sub": str(staff_user.id), "role": "admin"})
        status_code, res_tamper = client.get("/api/test/admin", token=fake_token)
        assert status_code == 403, f"Role tampering succeeded! Status: {status_code}"
        print("  -> JWT role spoofing prevented by database identity verification [PASSED]")

        # -------------------------------------------------------------
        # TEST 8: Workforce /api/auth/me Endpoint Verification
        # -------------------------------------------------------------
        print("\n[TEST 8] Workforce /api/auth/me Endpoint Verification")
        status_code, doc_me_data = client.get("/api/auth/me", token=doc_token)
        assert status_code == 200
        assert doc_me_data["role"] == "doctor"
        assert doc_me_data["profile"]["id"] is not None
        assert doc_me_data["profile"]["registration_number"] is not None
        print("  -> Doctor /api/auth/me returns User info + Doctor profile [PASSED]")

        status_code, nurse_me_data = client.get("/api/auth/me", token=nurse_token)
        assert status_code == 200
        assert nurse_me_data["role"] == "nurse"
        assert nurse_me_data["profile"]["id"] is not None
        print("  -> Nurse /api/auth/me returns User info + Nurse profile [PASSED]")

        status_code, staff_me_data = client.get("/api/auth/me", token=staff_token)
        assert status_code == 200
        assert staff_me_data["role"] == "staff"
        assert staff_me_data["profile"]["id"] is not None
        print("  -> Staff /api/auth/me returns User info + Staff profile [PASSED]")

        print("\n" + "=" * 70)
        print("ALL 8 AUTOMATED TEST SUITES PASSED PERFECTLY!")
        print("=" * 70)

    finally:
        db.close()


if __name__ == "__main__":
    run_tests()
