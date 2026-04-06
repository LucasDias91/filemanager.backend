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

    def list_all(self) -> list[File]:
        stmt = select(File).order_by(File.id)
        return list(self._db.scalars(stmt).all())
