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
    source: str = "booking"
    booking_id: int | None = None


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
    source: str | None = None
    booking_id: int | None = None


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
    source: str | None = "booking"
    booking_id: int | None = None

    model_config = ConfigDict(from_attributes=True)


class MedicineItemInput(BaseModel):
    medicine_id: int | None = None
    medicine_name: str
    quantity: int = 1
    price: float = 0.0


class RoomChargeInput(BaseModel):
    room_id: int | None = None
    room_number: str | None = None
    ward: str | None = None
    room_type: str | None = None
    days: int = 1
    price_per_day: float = 0.0
    total: float = 0.0


class AppointmentChargeInput(BaseModel):
    doctor_id: int | None = None
    doctor_name: str | None = None
    date: str | None = None
    charge: float = 0.0


class OtherChargeInput(BaseModel):
    description: str | None = None
    amount: float = 0.0


class ManualBillCreate(BaseModel):
    patient_id: str | int
    service_id: int
    duration: str | None = "1 Day"
    medicines: list[MedicineItemInput] | None = []
    room_charge: RoomChargeInput | None = None
    appointment: AppointmentChargeInput | None = None
    other_charges: OtherChargeInput | None = None
    discount: float = 0.0
    payment_status: str = "Unpaid"
    paid_amount: float = 0.0
    payment_method: str | None = "Cash"
    tax_rate: float = 5.0

