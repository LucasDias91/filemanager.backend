from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import Response

from app.api.deps import get_current_user, get_file_service
from app.models.user import User
from app.schemas.file import FileCreate, FileCreatedResponse, FileResponse
from app.services.errors import InvalidFileSecretError, StoredFileNotFoundError
from app.services.file_service import FileService, build_absolute_view_url

public_router = APIRouter(prefix="/files", tags=["files"])


@public_router.get("/raw/{stored_name}")
def get_raw_file(
    stored_name: str,
    secretKey: str = Query(..., description="Chave secreta devolvida no upload."),
    service: FileService = Depends(get_file_service),
) -> Response:
    try:
        data, content_type = service.read_public_file(stored_name, secretKey)
    except StoredFileNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="File not found") from exc
    except InvalidFileSecretError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Invalid secret") from exc

    media = content_type or "application/octet-stream"
    return Response(content=data, media_type=media)


router = APIRouter(prefix="/files", tags=["files"], dependencies=[Depends(get_current_user)])


@router.post(
    "",
    response_model=FileCreatedResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
)
async def create_file(
    current_user: User = Depends(get_current_user),
    file: UploadFile = File(...),
    service: FileService = Depends(get_file_service),
) -> FileCreatedResponse:
    raw = await file.read()
    name = (file.filename or "unnamed").strip() or "unnamed"
    if len(name) > 255:
        name = name[:255]

    ct = file.content_type
    if ct is not None:
        ct = ct.strip() or None
    if ct is not None and len(ct) > 50:
        ct = ct[:50]

    payload = FileCreate(
        user_id=current_user.id,
        original_name=name,
        content_type=ct,
        size=len(raw),
    )

    row = service.create(payload, file_bytes=raw)
    return FileCreatedResponse(
        id=row.id,
        url=build_absolute_view_url(row.stored_name, row.secret_key),
        secret_key=row.secret_key,
    )


@router.get("", response_model=list[FileResponse])
def list_files(service: FileService = Depends(get_file_service)) -> list[FileResponse]:
    rows = service.list_all()
    return [FileResponse.model_validate(r) for r in rows]
