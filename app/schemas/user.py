from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    name: str = Field(..., max_length=255, description="Nome completo")
    user_name: str = Field(..., max_length=100, description="Nome de utilizador (único)")
    password: str = Field(..., max_length=10, description="Palavra-passe")


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Identificador do utilizador")
    name: str = Field(..., description="Nome completo")
    user_name: str = Field(..., description="Nome de utilizador")
    is_active: bool = Field(..., description="Indica se a conta está ativa")
    create_at: datetime = Field(..., description="Data de criação do registo")
