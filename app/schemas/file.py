from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FileCreate(BaseModel):
    user_id: int = Field(..., ge=1)
    original_name: str = Field(..., max_length=255)
    content_type: str | None = Field(None, max_length=255)
    size: int = Field(..., ge=0)


class FileCreatedResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=True)

    id: int = Field(..., description="Identificador do arquivo na base de dados")
    url: str = Field(..., description="URL pública para descarregar o arquivo em /storage/…")
    secret_key: str = Field(
        serialization_alias="secretKey",
        description="Chave secreta para download, atualização ou eliminação sem JWT",
    )


class FileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    original_name: str
    stored_name: str
    content_type: str | None
    relative_location: str
    relative_url: str
    url: str
    relative_path: str
    size: int
    secret_key: str
    is_active: bool
    create_at: datetime
