from pydantic import BaseModel, ConfigDict, EmailStr


class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: str = "receptionist"


class UserLogin(BaseModel):
    email: str
    password: str
    role: str | None = None


class UserProfileUpdate(BaseModel):
    name: str | None = None
    username: str | None = None
    email: str | None = None
    phone: str | None = None
    avatar: str | None = None


class UserResponse(BaseModel):
    id: int
    name: str
    username: str | None = None
    email: str
    phone: str | None = None
    avatar: str | None = None
    role: str
    is_active: bool
    must_change_password: bool = False
    profile: dict | None = None

    model_config = ConfigDict(
        from_attributes=True
    )


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse