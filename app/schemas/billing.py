from datetime import date as dt_date
from pydantic import BaseModel, ConfigDict


class BillCreate(BaseModel):
    invoice_number: str
    patient_id: str | None = None
    patient_name: str
    patient_age: str | None = None
    patient_gender: str | None = None
    patient_phone: str | None = None
    patient_email: str | None = None
    address: str | None = None
    bill_type: str = "Patient"
    description: str | None = None
    doctor: str | None = None
    department: str | None = None
    date: dt_date
    subtotal: float = 0.0
    tax: float = 0.0
    discount: float = 0.0
    total_amount: float = 0.0
    paid_amount: float = 0.0
    payment_status: str = "Pending"
    payment_method: str | None = "Cash"
    items_json: str | None = None


class BillUpdate(BaseModel):
    patient_name: str | None = None
    patient_phone: str | None = None
    patient_email: str | None = None
    bill_type: str | None = None
    description: str | None = None
    doctor: str | None = None
    department: str | None = None
    date: dt_date | None = None
    subtotal: float | None = None
    tax: float | None = None
    discount: float | None = None
    total_amount: float | None = None
    paid_amount: float | None = None
    payment_status: str | None = None
    payment_method: str | None = None
    items_json: str | None = None


class BillResponse(BaseModel):
    id: int
    invoice_number: str
    patient_id: str | None
    patient_name: str
    patient_age: str | None
    patient_gender: str | None
    patient_phone: str | None
    patient_email: str | None
    address: str | None
    bill_type: str
    description: str | None
    doctor: str | None
    department: str | None
    date: dt_date
    subtotal: float
    tax: float
    discount: float
    total_amount: float
    paid_amount: float
    payment_status: str
    payment_method: str | None
    items_json: str | None

    model_config = ConfigDict(from_attributes=True)
