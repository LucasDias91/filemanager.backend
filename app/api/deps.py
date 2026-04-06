from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.repositories.file_repository import FileRepository
from app.repositories.user_repository import UserRepository
from app.services.file_service import FileService
from app.services.user_service import UserService


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(UserRepository(db))


def get_file_service(db: Session = Depends(get_db)) -> FileService:
    return FileService(FileRepository(db), UserRepository(db))
