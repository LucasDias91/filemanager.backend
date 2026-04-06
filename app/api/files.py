from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.api.deps import get_current_user, get_file_service
from app.schemas.file import FileCreate, FileResponse
from app.services.errors import UserNotFoundError
from app.services.file_service import FileService

router = APIRouter(prefix="/files", tags=["files"], dependencies=[Depends(get_current_user)])


@router.post("", response_model=FileResponse, status_code=status.HTTP_201_CREATED)
async def create_file(
    user_id: int = Form(..., ge=1),
    file: UploadFile = File(...),
    service: FileService = Depends(get_file_service),
) -> FileResponse:
    raw = await file.read()
    original_name = (file.filename or "unnamed").strip() or "unnamed"
    if len(original_name) > 255:
        original_name = original_name[:255]

    ct = file.content_type
    if ct is not None and len(ct) > 50:
        ct = ct[:50]

    payload = FileCreate(
        user_id=user_id,
        original_name=original_name,
        content_type=ct,
        size=len(raw),
    )

    try:
        row = service.create(payload, file_bytes=raw)
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User id={user_id} not found",
        ) from None

    return FileResponse.model_validate(row)


@router.get("", response_model=list[FileResponse])
def list_files(service: FileService = Depends(get_file_service)) -> list[FileResponse]:
    rows = service.list_all()
    return [FileResponse.model_validate(r) for r in rows]
