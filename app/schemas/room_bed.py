from pydantic import BaseModel, ConfigDict


class BedCreate(BaseModel):
    room_id: int | None = None
    bed_number: str
    status: str = "Available"
    patient_id: int | None = None
    patient_name: str | None = None
    patient_code: str | None = None
    admission_date: str | None = None
    daily_charge: float = 500.0


class BedUpdate(BaseModel):
    bed_number: str | None = None
    status: str | None = None
    patient_id: int | None = None
    patient_name: str | None = None
    patient_code: str | None = None
    admission_date: str | None = None
    daily_charge: float | None = None


class BedResponse(BaseModel):
    id: int
    room_id: int
    bed_number: str
    status: str
    patient_id: int | None = None
    patient_name: str | None = None
    patient_code: str | None = None
    admission_date: str | None = None
    daily_charge: float

    # Flat fields for frontend compatibility with Admissions.jsx
    room_number: str | None = None
    room_type: str | None = None
    floor: str | None = None
    ward: str | None = None
    department: str | None = None

    model_config = ConfigDict(from_attributes=True)


class RoomCreate(BaseModel):
    room_number: str
    ward: str
    room_type: str = "General"
    floor: str = "1st Floor"
    department: str | None = None
    daily_charge: float = 500.0
    status: str = "Active"
    beds: list[BedCreate] = []


class RoomUpdate(BaseModel):
    room_number: str | None = None
    ward: str | None = None
    room_type: str | None = None
    floor: str | None = None
    department: str | None = None
    daily_charge: float | None = None
    status: str | None = None


class RoomResponse(BaseModel):
    id: int
    room_number: str
    ward: str
    room_type: str
    floor: str
    department: str | None = None
    daily_charge: float
    status: str
    beds: list[BedResponse] = []

    model_config = ConfigDict(from_attributes=True)
