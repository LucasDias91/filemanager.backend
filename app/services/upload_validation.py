from __future__ import annotations

import io
import os
import re
import zipfile
from typing import Final

from fastapi import HTTPException, UploadFile, status

_MAX_UPLOAD_MB = int(os.environ.get("FILEMANAGER_MAX_UPLOAD_MB", "100"))
MAX_UPLOAD_BYTES: Final[int] = max(1, _MAX_UPLOAD_MB) * 1024 * 1024

_OLE_COMPOUND_MAGIC: Final[bytes] = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"

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
    {"jpg", "jpeg", "png", "webp", "pdf", "doc", "docx", "xls", "xlsx"}
)

_CANONICAL_MIME: Final[dict[str, str]] = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
    "pdf": "application/pdf",
    "doc": "application/msword",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "xls": "application/vnd.ms-excel",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}

_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
_BAD_NAME_RE = re.compile(r"[<>\"]|\.{2,}")

# OOXML: alguns geradores usam maiúsculas (ex.: Word/Document.xml); Word também usa document2.xml.
_RE_DOCX_MAIN = re.compile(r"(?i)word/document\d*\.xml$")
_RE_XLSX_WORKBOOK = re.compile(r"(?i)xl/workbook\.xml$")


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
            detail="Only jpg, jpeg, png, webp, pdf, doc, docx, xls, xlsx are allowed",
        )
    return name


def _zip_name_matches_any(data: bytes, pattern: re.Pattern[str]) -> bool:
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            for name in zf.namelist():
                norm = name.replace("\\", "/")
                if pattern.search(norm):
                    return True
    except (zipfile.BadZipFile, OSError):
        return False
    return False


def _infer_ooxml_extension(body: bytes) -> str | None:
    if not body.startswith(b"PK\x03\x04"):
        return None
    if _zip_name_matches_any(body, _RE_XLSX_WORKBOOK):
        return "xlsx"
    if _zip_name_matches_any(body, _RE_DOCX_MAIN):
        return "docx"
    return None


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
        return body.startswith(b"PK\x03\x04") and _zip_name_matches_any(body, _RE_DOCX_MAIN)
    if ext == "xlsx":
        return body.startswith(b"PK\x03\x04") and _zip_name_matches_any(body, _RE_XLSX_WORKBOOK)
    if ext in ("doc", "xls"):
        return len(body) >= 8 and body.startswith(_OLE_COMPOUND_MAGIC)
    return False


def validate_upload_body(
    *,
    original_filename: str | None,
    body: bytes,
) -> tuple[str, str]:
    """Valida extensão e assinatura do conteúdo. Não valida Content-Type do browser (varia muito; docx/xlsx costumam vir como application/zip)."""
    if not body:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file",
        )

    raw = (original_filename or "").strip() or "upload"
    base = os.path.basename(raw.replace("\\", "/"))
    if "." not in base:
        inferred = _infer_ooxml_extension(body)
        if inferred:
            raw = f"{base}.{inferred}" if base and base not in (".", "..") else f"upload.{inferred}"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File name must include an extension (e.g. .docx, .xlsx)",
            )

    display_name = _validate_name_and_ext(raw)
    ext, _ = _extension_segments(display_name)
    if not _body_matches_extension(ext, body):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content does not match declared type (signature check failed)",
        )

    canonical = _CANONICAL_MIME[ext]
    return display_name, canonical
