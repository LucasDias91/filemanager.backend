from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    name: str = Field(..., max_length=255)
    user_name: str = Field(..., max_length=100)
    password: str = Field(..., max_length=10)
    is_active: bool = True


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    user_name: str
    is_active: bool
    create_at: datetime
