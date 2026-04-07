from __future__ import annotations

import io
import os
import re
import zipfile
from typing import Final

from fastapi import HTTPException, UploadFile, status

_MAX_UPLOAD_MB = int(os.environ.get("FILEMANAGER_MAX_UPLOAD_MB", "100"))
MAX_UPLOAD_BYTES: Final[int] = max(1, _MAX_UPLOAD_MB) * 1024 * 1024

_DANGEROUS_SEGMENTS: Final[frozenset[str]] = frozenset(
    {
        "exe",
        "msi",
        "bat",
        "cmd",
        "sh",
        "bash",
        "ps1",
        "psm1",
        "app",
        "jar",
        "php",
        "asp",
        "aspx",
        "jsp",
        "js",
        "mjs",
        "cjs",
        "ts",
        "mts",
        "cts",
        "zip",
        "rar",
        "7z",
        "com",
        "scr",
        "pif",
        "vbs",
        "wsf",
        "dll",
        "dylib",
        "so",
    }
)

_ALLOWED_EXT: Final[frozenset[str]] = frozenset(
    {"jpg", "jpeg", "png", "webp", "pdf", "docx", "xlsx"}
)

_ALLOWED_MIME_BY_EXT: Final[dict[str, frozenset[str]]] = {
    "jpg": frozenset({"image/jpeg"}),
    "jpeg": frozenset({"image/jpeg"}),
    "png": frozenset({"image/png"}),
    "webp": frozenset({"image/webp"}),
    "pdf": frozenset({"application/pdf"}),
    "docx": frozenset(
        {
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        }
    ),
    "xlsx": frozenset(
        {
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        }
    ),
}

_CANONICAL_MIME: Final[dict[str, str]] = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}

_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
_BAD_NAME_RE = re.compile(r"[<>\"]|\.{2,}")


async def read_upload_with_limit(upload: UploadFile, limit: int = MAX_UPLOAD_BYTES) -> bytes:
    out = bytearray()
    while True:
        chunk = await upload.read(64 * 1024)
        if not chunk:
            break
        if len(out) + len(chunk) > limit:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds maximum size of {limit // (1024 * 1024)}MB",
            )
        out.extend(chunk)
    return bytes(out)


def _normalize_client_mime(raw: str | None) -> str | None:
    if raw is None:
        return None
    s = raw.strip().lower()
    if not s:
        return None
    if ";" in s:
        s = s.split(";", 1)[0].strip()
    return s[:50] if s else None


def _sanitize_display_name(filename: str) -> str:
    base = os.path.basename(filename.replace("\\", "/"))
    if not base or base in (".", ".."):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file name",
        )
    if _BAD_NAME_RE.search(base):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid characters in file name",
        )
    cleaned = _CONTROL_RE.sub("", base).strip()
    if not cleaned:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file name",
        )
    if len(cleaned) > 255:
        cleaned = cleaned[:255]
    return cleaned


def _extension_segments(display_name: str) -> tuple[str, list[str]]:
    parts = display_name.split(".")
    if len(parts) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A file extension is required",
        )
    ext = parts[-1].lower().strip()
    if not ext or len(ext) > 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file extension",
        )
    inner = [p.lower() for p in parts[1:-1]]
    return ext, inner


def _validate_name_and_ext(display_name: str) -> str:
    name = _sanitize_display_name(display_name)
    ext, inner_segments = _extension_segments(name)
    for seg in inner_segments:
        if seg in _DANGEROUS_SEGMENTS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Disallowed file name (suspicious extension chain)",
            )
    if ext in _DANGEROUS_SEGMENTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File type not allowed",
        )
    if ext not in _ALLOWED_EXT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only jpg, jpeg, png, webp, pdf, docx, xlsx are allowed",
        )
    return name


def _zip_has_file(data: bytes, member: str) -> bool:
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            return member in zf.namelist()
    except (zipfile.BadZipFile, OSError):
        return False


def _body_matches_extension(ext: str, body: bytes) -> bool:
    if ext in ("jpg", "jpeg"):
        return body.startswith(b"\xff\xd8\xff")
    if ext == "png":
        return len(body) >= 8 and body.startswith(b"\x89PNG\r\n\x1a\n")
    if ext == "webp":
        return len(body) >= 12 and body.startswith(b"RIFF") and body[8:12] == b"WEBP"
    if ext == "pdf":
        return body.startswith(b"%PDF")
    if ext == "docx":
        return body.startswith(b"PK\x03\x04") and _zip_has_file(body, "word/document.xml")
    if ext == "xlsx":
        return body.startswith(b"PK\x03\x04") and _zip_has_file(body, "xl/workbook.xml")
    return False


def validate_upload_body(
    *,
    original_filename: str | None,
    client_content_type: str | None,
    body: bytes,
) -> tuple[str, str]:
    if not body:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file",
        )

    display_name = _validate_name_and_ext(
        (original_filename or "unnamed").strip() or "unnamed"
    )
    ext, _ = _extension_segments(display_name)
    if not _body_matches_extension(ext, body):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content does not match declared type (signature check failed)",
        )

    client_mime = _normalize_client_mime(client_content_type)
    allowed_mimes = _ALLOWED_MIME_BY_EXT[ext]
    if client_mime is not None and client_mime not in allowed_mimes:
        if client_mime != "application/octet-stream":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Content-Type not allowed for this file type",
            )

    canonical = _CANONICAL_MIME[ext]
    return display_name, canonical
