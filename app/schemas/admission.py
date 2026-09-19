from datetime import date, time
from pydantic import BaseModel, ConfigDict


class AdmissionCreate(BaseModel):
    admission_number: str
    patient_id: int
    doctor_id: int
    room_bed_id: int | None = None
    admission_date: date
    admission_time: time | None = None
    admission_type: str = "Planned"
    reason: str | None = None
    diagnosis: str | None = None
    status: str = "Admitted"
    remarks: str | None = None


class AdmissionUpdate(BaseModel):
    admission_number: str | None = None
    patient_id: int | None = None
    doctor_id: int | None = None
    room_bed_id: int | None = None
    admission_date: date | None = None
    admission_time: time | None = None
    admission_type: str | None = None
    reason: str | None = None
    diagnosis: str | None = None
    discharge_date: date | None = None
    discharge_time: time | None = None
    discharge_summary: str | None = None
    discharge_status: str | None = None
    status: str | None = None
    remarks: str | None = None


class AdmissionResponse(BaseModel):
    id: int
    admission_number: str
    patient_id: int
    doctor_id: int
    room_bed_id: int | None
    admission_date: date
    admission_time: time | None
    admission_type: str
    reason: str | None
    diagnosis: str | None
    discharge_date: date | None
    discharge_time: time | None
    discharge_summary: str | None
    discharge_status: str | None
    status: str
    remarks: str | None

    # Joined fields for frontend
    patient_name: str | None = None
    patient_registration_number: str | None = None
    doctor_name: str | None = None
    department: str | None = None
    ward: str | None = None
    room_number: str | None = None
    bed_number: str | None = None

    model_config = ConfigDict(from_attributes=True)
