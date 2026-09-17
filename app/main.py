from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.models import User, Patient, Staff, Service

from app.routers.auth import router as auth_router
from app.routers.test_auth import router as test_auth_router
from app.routers.users import router as users_router
from app.routers.patients import router as patients_router
from app.routers.staff import router as staff_router
from app.routers.services import router as services_router
from app.models.booking import Booking
from app.routers.bookings import router as bookings_router

Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Hospital Management System API",
    description="Backend API for Hospital Management System",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router)
app.include_router(test_auth_router)
app.include_router(users_router)
app.include_router(patients_router)
app.include_router(staff_router)
app.include_router(services_router)
app.include_router(bookings_router)

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