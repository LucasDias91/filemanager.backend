from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FileCreate(BaseModel):
    user_id: int = Field(..., ge=1)
    original_name: str = Field(..., max_length=255)
    content_type: str | None = Field(None, max_length=50)
    size: int = Field(..., ge=0)


class FileCreatedResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=True)

    id: int
    url: str
    secret_key: str = Field(serialization_alias="secretKey")


class FileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    original_name: str
    stored_name: str
    content_type: str | None
    relative_location: str
    relative_url: str
    relative_path: str
    size: int
    secret_key: str
    is_active: bool
    create_at: datetime
