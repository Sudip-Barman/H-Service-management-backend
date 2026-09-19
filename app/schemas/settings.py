from typing import Any
from pydantic import BaseModel, ConfigDict


class SettingsResponse(BaseModel):
    settings: dict[str, Any]

    model_config = ConfigDict(from_attributes=True)


class SettingsUpdate(BaseModel):
    settings: dict[str, Any]
