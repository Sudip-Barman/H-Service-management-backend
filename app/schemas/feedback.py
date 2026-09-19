from pydantic import BaseModel, ConfigDict


class FeedbackCreate(BaseModel):
    feedback_code: str | None = None
    patient: str
    email: str | None = None
    service: str
    rating: int = 5
    status: str = "New"
    date: str
    comment: str | None = None


class FeedbackUpdate(BaseModel):
    patient: str | None = None
    email: str | None = None
    service: str | None = None
    rating: int | None = None
    status: str | None = None
    comment: str | None = None


class FeedbackResponse(BaseModel):
    id: int
    feedback_code: str
    patient: str
    email: str | None
    service: str
    rating: int
    status: str
    date: str
    comment: str | None

    model_config = ConfigDict(from_attributes=True)
