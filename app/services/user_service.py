from datetime import UTC, datetime

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate


class UserService:
    def __init__(self, user_repository: UserRepository) -> None:
        self._users = user_repository

    def create(self, data: UserCreate) -> User:
        now = datetime.now(UTC)
        entity = User(
            name=data.name,
            user_name=data.user_name,
            password=data.password,
            is_active=data.is_active,
            create_at=now,
        )
        return self._users.create(entity)

    def list_all(self) -> list[User]:
        return self._users.list_all()
