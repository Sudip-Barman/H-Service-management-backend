from pydantic import BaseModel, ConfigDict


class EmergencyCreate(BaseModel):
    emergency_code: str
    name: str
    age: str | None = None
    gender: str = "Male"
    blood_group: str | None = None
    phone: str | None = None
    emergency_contact: str | None = None
    emergency_phone: str | None = None
    arrival_time: str | None = None
    triage: str = "Urgent"
    status: str = "Under Treatment"
    condition_summary: str | None = None
    symptoms: str | None = None
    assigned_doctor: str | None = None
    department: str | None = "Emergency Medicine"
    room: str | None = None
    allergies: str | None = None
    notes: str | None = None


class EmergencyUpdate(BaseModel):
    name: str | None = None
    age: str | None = None
    gender: str | None = None
    blood_group: str | None = None
    phone: str | None = None
    emergency_contact: str | None = None
    emergency_phone: str | None = None
    arrival_time: str | None = None
    triage: str | None = None
    status: str | None = None
    condition_summary: str | None = None
    symptoms: str | None = None
    assigned_doctor: str | None = None
    department: str | None = None
    room: str | None = None
    allergies: str | None = None
    notes: str | None = None


class EmergencyResponse(BaseModel):
    id: int
    emergency_code: str
    name: str
    age: str | None
    gender: str
    blood_group: str | None
    phone: str | None
    emergency_contact: str | None
    emergency_phone: str | None
    arrival_time: str | None
    triage: str
    status: str
    condition_summary: str | None
    symptoms: str | None
    assigned_doctor: str | None
    department: str | None
    room: str | None
    allergies: str | None
    notes: str | None

    model_config = ConfigDict(from_attributes=True)
