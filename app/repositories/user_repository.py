from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, user: User) -> User:
        self._db.add(user)
        self._db.commit()
        self._db.refresh(user)
        return user

    def get_by_id(self, user_id: int) -> User | None:
        return self._db.get(User, user_id)

    def list_all(self) -> list[User]:
        stmt = select(User).order_by(User.id)
        return list(self._db.scalars(stmt).all())
