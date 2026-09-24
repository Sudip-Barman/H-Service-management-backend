from pydantic import BaseModel, ConfigDict


class NotificationCreate(BaseModel):
    title: str
    message: str
    type: str = "General"
    priority: str = "Normal"
    department: str | None = None
    recipient: str | None = "All Clinical Staff"
    date: str | None = None
    time: str | None = None
    read: bool = False
    recipient_user_id: int | None = None
    recipient_role: str | None = None
    recipient_mode: str | None = "single"  # single, all_staff, selected
    recipient_user_ids: list[int] | None = None
    related_entity_type: str | None = None
    related_entity_id: int | None = None
    action_url: str | None = None


class NotificationUpdate(BaseModel):
    title: str | None = None
    message: str | None = None
    type: str | None = None
    priority: str | None = None
    department: str | None = None
    recipient: str | None = None
    read: bool | None = None
    recipient_user_id: int | None = None
    recipient_role: str | None = None
    related_entity_type: str | None = None
    related_entity_id: int | None = None
    action_url: str | None = None


class NotificationResponse(BaseModel):
    id: int
    title: str
    message: str
    type: str
    priority: str
    department: str | None
    recipient: str | None
    date: str | None
    time: str | None
    read: bool
    recipient_user_id: int | None = None
    recipient_role: str | None = None
    related_entity_type: str | None = None
    related_entity_id: int | None = None
    action_url: str | None = None

    model_config = ConfigDict(from_attributes=True)
