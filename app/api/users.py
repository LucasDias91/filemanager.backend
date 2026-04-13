from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.api.deps import get_current_user, get_user_service
from app.schemas.user import UserCreate, UserResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "",
    summary="Criar utilizador",
    description="Regista um novo utilizador.",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    payload: UserCreate,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    try:
        user = service.create(payload)
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="user_name already exists",
        ) from exc
    return UserResponse.model_validate(user)


@router.get(
    "",
    summary="Listar utilizadores",
    description="Lista todos os utilizadores (requer JWT Bearer).",
    response_model=list[UserResponse],
)
def list_users(
    _: object = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> list[UserResponse]:
    users = service.list_all()
    return [UserResponse.model_validate(u) for u in users]
