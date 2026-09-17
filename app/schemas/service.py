from pydantic import BaseModel, ConfigDict


class ServiceCreate(BaseModel):
    name: str
    category: str
    description: str | None = None
    price: float = 0
    duration: str | None = None
    is_active: bool = True


class ServiceResponse(BaseModel):
    id: int
    name: str
    category: str
    description: str | None
    price: float
    duration: str | None
    is_active: bool

    model_config = ConfigDict(
        from_attributes=True
    )