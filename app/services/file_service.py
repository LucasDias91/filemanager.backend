from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote

from app.models.file import File
from app.repositories.file_repository import FileRepository
from app.repositories.user_repository import UserRepository
from app.schemas.file import FileCreate
from app.services.errors import UserNotFoundError

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
UPLOAD_ROOT = _PROJECT_ROOT / "storage"

PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
STORAGE_URL_PATH = "/storage"


def build_absolute_storage_url(stored_name: str) -> str:
    segment = quote(stored_name, safe="")
    return f"{PUBLIC_BASE_URL}{STORAGE_URL_PATH}/{segment}"


class FileService:
    def __init__(
        self,
        file_repository: FileRepository,
        user_repository: UserRepository,
    ) -> None:
        self._files = file_repository
        self._users = user_repository

    @staticmethod
    def _safe_extension(original_name: str) -> str:
        suffix = Path(original_name).suffix
        if not suffix or len(suffix) > 20:
            return ""
        if not all(c.isalnum() or c == "." for c in suffix):
            return ""
        return suffix.lower()

    @classmethod
    def _make_stored_name(cls, original_name: str) -> str:
        return f"{uuid.uuid4()}{cls._safe_extension(original_name)}"

    @staticmethod
    def _build_relative_url(stored_name: str) -> str:
        return f"{STORAGE_URL_PATH}/{stored_name}"

    def create(self, data: FileCreate, file_bytes: bytes) -> File:
        if self._users.get_by_id(data.user_id) is None:
            raise UserNotFoundError(data.user_id)

        stored_name = self._make_stored_name(data.original_name)
        secret_key = str(uuid.uuid4())
        now = datetime.now(UTC)

        relative_location = stored_name
        relative_url = self._build_relative_url(stored_name)

        UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
        dest_path = UPLOAD_ROOT / stored_name
        dest_path.write_bytes(file_bytes)

        entity = File(
            user_id=data.user_id,
            original_name=data.original_name,
            stored_name=stored_name,
            content_type=data.content_type,
            relative_location=relative_location,
            relative_url=relative_url,
            relative_path="",
            size=len(file_bytes),
            secret_key=secret_key,
            is_active=True,
            create_at=now,
        )
        return self._files.create(entity)

    def list_all(self) -> list[File]:
        return self._files.list_all()

    def get_file_by_secret_key(self, secret_key: str) -> tuple[str, str, str | None, bytes] | None:
        row = self._files.get_by_secret_key(secret_key)
        if row is None:
            return None

        path = UPLOAD_ROOT / row.stored_name
        if not path.is_file():
            return None

        return (row.original_name, row.stored_name, row.content_type, path.read_bytes())

    def get_metadata_by_secret_key(self, secret_key: str) -> File | None:
        return self._files.get_by_secret_key(secret_key)

    def delete_file_by_secret_key(self, secret_key: str) -> bool:
        row = self._files.get_by_secret_key(secret_key)
        if row is None:
            return False

        path = UPLOAD_ROOT / row.stored_name
        if path.exists():
            path.unlink()

        self._files.delete(row)
        return True

    def update_file_by_secret_key(
        self,
        secret_key: str,
        *,
        original_name: str,
        content_type: str | None,
        file_bytes: bytes,
    ) -> File | None:
        row = self._files.get_by_secret_key(secret_key)
        if row is None:
            return None

        path = UPLOAD_ROOT / row.stored_name
        path.write_bytes(file_bytes)

        row.original_name = original_name
        row.content_type = content_type
        row.size = len(file_bytes)
        return self._files.update(row)
