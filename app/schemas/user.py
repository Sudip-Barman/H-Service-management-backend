from pydantic import BaseModel, ConfigDict, EmailStr


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "receptionist"


class UserLogin(BaseModel):
    email: EmailStr
    password: str
    role: str | None = None


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    is_active: bool

    model_config = ConfigDict(
        from_attributes=True
    )


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse