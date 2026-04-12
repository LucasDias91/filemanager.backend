from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(..., max_length=100, description="Nome de utilizador")
    password: str = Field(..., max_length=10, description="Palavra-passe")


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="Token JWT de acesso")
    token_type: str = Field(default="bearer", description="Tipo do token (sempre bearer)")
    expires_in: int = Field(..., description="Validade do token em segundos")
