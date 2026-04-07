from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.file import File


class FileRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, file_row: File) -> File:
        self._db.add(file_row)
        self._db.commit()
        self._db.refresh(file_row)
        return file_row

    def get_by_stored_name(self, stored_name: str) -> File | None:
        stmt = select(File).where(File.stored_name == stored_name)
        return self._db.scalar(stmt)

    def get_by_secret_key(self, secret_key: str) -> File | None:
        stmt = select(File).where(File.secret_key == secret_key)
        return self._db.scalar(stmt)

    def list_all(self) -> list[File]:
        stmt = select(File).order_by(File.id)
        return list(self._db.scalars(stmt).all())
