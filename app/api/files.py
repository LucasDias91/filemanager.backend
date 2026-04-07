from urllib.parse import quote

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import Response

from app.api.deps import get_current_user, get_file_service
from app.models.user import User
from app.schemas.file import FileCreate, FileCreatedResponse, FileResponse
from app.services.file_service import FileService, build_absolute_storage_url

router = APIRouter(prefix="/files", tags=["files"], dependencies=[Depends(get_current_user)])
public_router = APIRouter(prefix="/files", tags=["files"])


@router.post(
    "/upload",
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
        url=build_absolute_storage_url(row.stored_name),
        secret_key=row.secret_key,
    )


@router.get("", response_model=list[FileResponse])
def list_files(service: FileService = Depends(get_file_service)) -> list[FileResponse]:
    rows = service.list_all()
    return [
        FileResponse.model_validate(
            {
                **r.__dict__,
                "url": build_absolute_storage_url(r.stored_name),
            }
        )
        for r in rows
    ]


@public_router.get("/download")
def download_file_by_key(
    key: str = Query(..., description="SecretKey retornada no upload."),
    service: FileService = Depends(get_file_service),
) -> Response:
    file_data = service.get_file_by_secret_key(key)
    if file_data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    original_name, _, content_type, data = file_data
    media_type = content_type or "application/octet-stream"
    encoded_name = quote(original_name)
    headers = {"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_name}"}
    return Response(content=data, media_type=media_type, headers=headers)


@public_router.get("/key/{secretKey}", response_model=FileCreatedResponse, response_model_by_alias=True)
def get_file_by_key(
    secretKey: str,
    service: FileService = Depends(get_file_service),
) -> FileCreatedResponse:
    row = service.get_metadata_by_secret_key(secretKey)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    return FileCreatedResponse(
        id=row.id,
        url=build_absolute_storage_url(row.stored_name),
        secret_key=row.secret_key,
    )


@public_router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def delete_file_by_key(
    key: str = Query(..., description="SecretKey retornada no upload."),
    service: FileService = Depends(get_file_service),
) -> Response:
    deleted = service.delete_file_by_secret_key(key)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@public_router.put(
    "/upload",
    response_model=FileCreatedResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_200_OK,
)
async def update_file_by_key(
    key: str = Query(..., description="SecretKey retornada no upload."),
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

    row = service.update_file_by_secret_key(
        key,
        original_name=name,
        content_type=ct,
        file_bytes=raw,
    )
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    return FileCreatedResponse(
        id=row.id,
        url=build_absolute_storage_url(row.stored_name),
        secret_key=row.secret_key,
    )
