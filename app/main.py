from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
import app.models
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from app.routers.auth import router as auth_router
from app.routers.test_auth import router as test_auth_router
from app.routers.users import router as users_router
from app.routers.patients import router as patients_router, legacy_router as legacy_patients_router
from app.routers.staff import router as staff_router
from app.routers.services import router as services_router
from app.routers.bookings import router as bookings_router
from app.routers.doctors import router as doctors_router
from app.routers.nurses import router as nurses_router
from app.routers.rooms_beds import router as rooms_beds_router
from app.routers.admissions import router as admissions_router
from app.routers.schedules import router as schedules_router
from app.routers.shifts import router as shifts_router
from app.routers.attendance import router as attendance_router
from app.routers.blood_bank import router as blood_bank_router
from app.routers.medicines import router as medicines_router
from app.routers.emergency import router as emergency_router
from app.routers.inventory import router as inventory_router
from app.routers.billing import router as billing_router
from app.routers.followups import router as followups_router
from app.routers.requests import router as requests_router
from app.routers.notifications import router as notifications_router
from app.routers.feedback import router as feedback_router
from app.routers.dashboard import router as dashboard_router
from app.routers.settings import router as settings_router
from app.routers.assets import router as assets_router
from app.seed_data import seed

Base.metadata.create_all(bind=engine)
try:
    seed()
except Exception:
    pass

app = FastAPI(
    title="Hospital Management System API",
    description="Backend API for Hospital Management System",
    version="1.0.0"
)

BASE_DIR = Path(__file__).resolve().parent.parent

UPLOADS_DIR = BASE_DIR / "uploads"

app.mount(
    "/uploads",
    StaticFiles(directory=UPLOADS_DIR),
    name="uploads",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:3000",
    ],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:[0-9]+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(test_auth_router)
app.include_router(users_router)
app.include_router(patients_router)
app.include_router(legacy_patients_router)
app.include_router(staff_router)
app.include_router(services_router)
app.include_router(bookings_router)
app.include_router(doctors_router)
app.include_router(nurses_router)
app.include_router(rooms_beds_router)
app.include_router(admissions_router)
app.include_router(schedules_router)
app.include_router(shifts_router)
app.include_router(attendance_router)
app.include_router(blood_bank_router)
app.include_router(medicines_router)
app.include_router(emergency_router)
app.include_router(inventory_router)
app.include_router(billing_router)
app.include_router(followups_router)
app.include_router(requests_router)
app.include_router(notifications_router)
app.include_router(feedback_router)
app.include_router(dashboard_router)
app.include_router(settings_router)
app.include_router(assets_router)


@app.get("/")
def root():
    return {
        "message": "Hospital Management System API is running"
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "database": "connected"
    }