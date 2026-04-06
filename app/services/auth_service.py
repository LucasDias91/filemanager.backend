import os
from datetime import UTC, datetime, timedelta

import jwt

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.errors import InvalidCredentialsError, InvalidTokenError

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-me")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24


class AuthService:
    def __init__(self, user_repository: UserRepository) -> None:
        self._users = user_repository

    def authenticate(self, username: str, password: str) -> str:
        user = self._users.get_by_user_name(username)
        if user is None or user.password != password or not user.is_active:
            raise InvalidCredentialsError()
        return self._create_token(user.id)

    def validate_token(self, token: str) -> int:
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            user_id = payload.get("userId")
            if not isinstance(user_id, int):
                raise InvalidTokenError()
            return user_id
        except jwt.InvalidTokenError as exc:
            raise InvalidTokenError() from exc

    def _create_token(self, user_id: int) -> str:
        expires_at = datetime.now(UTC) + timedelta(hours=JWT_EXPIRATION_HOURS)
        payload = {"userId": user_id, "exp": expires_at}
        return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
