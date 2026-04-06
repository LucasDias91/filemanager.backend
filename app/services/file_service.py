from __future__ import annotations

import os
import secrets
import uuid
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote

from app.models.file import File
from app.repositories.file_repository import FileRepository
from app.repositories.user_repository import UserRepository
from app.schemas.file import FileCreate
from app.services.errors import (
    InvalidFileSecretError,
    StoredFileNotFoundError,
    UserNotFoundError,
)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
UPLOAD_ROOT = _PROJECT_ROOT / "uploads"

PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
FILES_RAW_PATH_PREFIX = "/api/files/raw"


def build_absolute_view_url(stored_name: str, secret_key: str) -> str:
    path = f"{FILES_RAW_PATH_PREFIX}/{stored_name}"
    return f"{PUBLIC_BASE_URL}{path}?secretKey={quote(secret_key, safe='')}"


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
        return f"{FILES_RAW_PATH_PREFIX}/{stored_name}"

    @staticmethod
    def _is_safe_stored_name(stored_name: str) -> bool:
        if not stored_name or len(stored_name) > 255:
            return False
        if "/" in stored_name or "\\" in stored_name or stored_name.startswith("."):
            return False
        return True

    def read_public_file(self, stored_name: str, secret_key: str) -> tuple[bytes, str | None]:
        if not self._is_safe_stored_name(stored_name):
            raise StoredFileNotFoundError()

        row = self._files.get_by_stored_name(stored_name)
        if row is None:
            raise StoredFileNotFoundError()

        if not secrets.compare_digest(row.secret_key, secret_key):
            raise InvalidFileSecretError()

        path = UPLOAD_ROOT / stored_name
        if not path.is_file():
            raise StoredFileNotFoundError()

        return path.read_bytes(), row.content_type

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
