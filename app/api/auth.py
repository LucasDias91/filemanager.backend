from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_auth_service
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth_service import JWT_EXPIRATION_HOURS, AuthService
from app.services.errors import InvalidCredentialsError

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    summary="Iniciar sessão",
    description="Autentica com nome de utilizador e palavra-passe e devolve um token JWT.",
    response_model=TokenResponse,
)
def login(
    payload: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    try:
        token = auth_service.authenticate(payload.username, payload.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        ) from exc

    return TokenResponse(
        access_token=token,
        expires_in=JWT_EXPIRATION_HOURS * 3600,
    )
