from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class ServiceCreate(BaseModel):
    name: str
    category: str
    description: str | None = None
    price: float = 0.0
    staff_required: int = 1
    available_staff: int = 0
    bookings: int = 0
    rating: float = 0.0
    duration: str | None = None
    is_active: bool = True

    @model_validator(mode="before")
    @classmethod
    def handle_camel_case(cls, values):
        if isinstance(values, dict):
            if "availableStaff" in values and "available_staff" not in values:
                values["available_staff"] = values["availableStaff"]
            if "staffRequired" in values and "staff_required" not in values:
                values["staff_required"] = values["staffRequired"]
        return values

    @field_validator("price", "rating", mode="before")
    @classmethod
    def coerce_float(cls, v):
        if v is None or v == "":
            return 0.0
        try:
            return float(v)
        except (ValueError, TypeError):
            return 0.0

    @field_validator("staff_required", "available_staff", "bookings", mode="before")
    @classmethod
    def coerce_int(cls, v):
        if v is None or v == "":
            return 0
        try:
            return int(float(v))
        except (ValueError, TypeError):
            return 0


class ServiceUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    description: str | None = None
    price: float | None = None
    staff_required: int | None = None
    available_staff: int | None = None
    bookings: int | None = None
    rating: float | None = None
    duration: str | None = None
    is_active: bool | None = None

    @model_validator(mode="before")
    @classmethod
    def handle_camel_case(cls, values):
        if isinstance(values, dict):
            if "availableStaff" in values and "available_staff" not in values:
                values["available_staff"] = values["availableStaff"]
            if "staffRequired" in values and "staff_required" not in values:
                values["staff_required"] = values["staffRequired"]
        return values

    @field_validator("price", "rating", mode="before")
    @classmethod
    def coerce_float(cls, v):
        if v is None or v == "":
            return None
        try:
            return float(v)
        except (ValueError, TypeError):
            return None

    @field_validator("staff_required", "available_staff", "bookings", mode="before")
    @classmethod
    def coerce_int(cls, v):
        if v is None or v == "":
            return None
        try:
            return int(float(v))
        except (ValueError, TypeError):
            return None


class ServiceResponse(BaseModel):
    id: int
    name: str
    category: str
    description: str | None
    price: float
    staff_required: int = 1
    available_staff: int = 0
    bookings: int = 0
    rating: float = 0.0
    duration: str | None
    is_active: bool

    model_config = ConfigDict(
        from_attributes=True
    )