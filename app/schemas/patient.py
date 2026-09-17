from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


# =========================================================
# PATIENT CREATE
# =========================================================

class PatientCreate(BaseModel):
    """
    Data required when creating a patient.

    registration_number is intentionally NOT included.
    It is generated automatically by the backend.
    """

    first_name: str = Field(
        min_length=1,
        max_length=100
    )

    middle_name: str | None = Field(
        default=None,
        max_length=100
    )

    last_name: str | None = Field(
        default=None,
        max_length=100
    )

    date_of_birth: date | None = None

    age: int | None = Field(
        default=None,
        ge=0,
        le=150
    )

    gender: str = Field(
        min_length=1,
        max_length=20
    )

    blood_group: str | None = Field(
        default=None,
        max_length=10
    )

    phone: str = Field(
        min_length=1,
        max_length=20
    )

    email: str | None = Field(
        default=None,
        max_length=150
    )

    address: str | None = Field(
        default=None,
        max_length=255
    )

    city: str | None = Field(
        default=None,
        max_length=100
    )

    state: str | None = Field(
        default=None,
        max_length=100
    )

    postal_code: str | None = Field(
        default=None,
        max_length=20
    )

    emergency_contact_name: str | None = Field(
        default=None,
        max_length=100
    )

    emergency_contact_phone: str | None = Field(
        default=None,
        max_length=20
    )

    emergency_contact_relation: str | None = Field(
        default=None,
        max_length=50
    )

    occupation: str | None = Field(
        default=None,
        max_length=100
    )

    marital_status: str | None = Field(
        default=None,
        max_length=30
    )

    nationality: str | None = Field(
        default=None,
        max_length=50
    )

    registration_date: date | None = None

    status: str = Field(
        default="Active",
        max_length=30
    )

    patient_problem: str = Field(
        min_length=1
    )

    digital_signature: str | None = None


# =========================================================
# PATIENT UPDATE
# =========================================================

class PatientUpdate(BaseModel):
    """
    Data allowed when updating an existing patient.

    registration_number is intentionally NOT included.
    Once generated, the registration number should not change.
    """

    first_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100
    )

    middle_name: str | None = Field(
        default=None,
        max_length=100
    )

    last_name: str | None = Field(
        default=None,
        max_length=100
    )

    date_of_birth: date | None = None

    age: int | None = Field(
        default=None,
        ge=0,
        le=150
    )

    gender: str | None = Field(
        default=None,
        max_length=20
    )

    blood_group: str | None = Field(
        default=None,
        max_length=10
    )

    phone: str | None = Field(
        default=None,
        max_length=20
    )

    email: str | None = Field(
        default=None,
        max_length=150
    )

    address: str | None = Field(
        default=None,
        max_length=255
    )

    city: str | None = Field(
        default=None,
        max_length=100
    )

    state: str | None = Field(
        default=None,
        max_length=100
    )

    postal_code: str | None = Field(
        default=None,
        max_length=20
    )

    emergency_contact_name: str | None = Field(
        default=None,
        max_length=100
    )

    emergency_contact_phone: str | None = Field(
        default=None,
        max_length=20
    )

    emergency_contact_relation: str | None = Field(
        default=None,
        max_length=50
    )

    occupation: str | None = Field(
        default=None,
        max_length=100
    )

    marital_status: str | None = Field(
        default=None,
        max_length=30
    )

    nationality: str | None = Field(
        default=None,
        max_length=50
    )

    registration_date: date | None = None

    status: str | None = Field(
        default=None,
        max_length=30
    )

    patient_problem: str | None = None

    digital_signature: str | None = None


# =========================================================
# PATIENT RESPONSE
# =========================================================

class PatientResponse(BaseModel):
    """
    Data returned by the API.
    """

    model_config = ConfigDict(
        from_attributes=True
    )

    id: int

    registration_number: str

    registration_date: date

    status: str

    first_name: str

    middle_name: str | None

    last_name: str | None

    date_of_birth: date | None

    age: int | None

    gender: str

    blood_group: str | None

    occupation: str | None

    marital_status: str | None

    nationality: str | None

    phone: str

    email: str | None

    address: str | None

    city: str | None

    state: str | None

    postal_code: str | None

    emergency_contact_name: str | None

    emergency_contact_phone: str | None

    emergency_contact_relation: str | None

    patient_problem: str

    digital_signature: str | None

    created_at: datetime

    updated_at: datetime