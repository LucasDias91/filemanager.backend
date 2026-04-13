from urllib.parse import quote

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import Response

from app.api.deps import get_current_user, get_file_service
from app.models.file import File as FileModel
from app.models.user import User
from app.schemas.file import FileCreate, FileCreatedResponse, FileResponse
from app.services.file_service import FileService, build_absolute_storage_url
from app.services.upload_validation import read_upload_with_limit, validate_upload_body

router = APIRouter(prefix="/files", tags=["files"], dependencies=[Depends(get_current_user)])


def _file_meta_for_user_or_404(
    service: FileService, secret_key: str, user_id: int
) -> FileModel:
    row = service.get_metadata_by_secret_key(secret_key)
    if row is None or row.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return row


@router.post(
    "/upload",
    summary="Enviar arquivo",
    description=(
        "Recebe o arquivo em multipart/form-data (campo `file`). "
        "Requer JWT Bearer; o dono do arquivo é o utilizador do token."
    ),
    response_model=FileCreatedResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
)
async def create_file(
    current_user: User = Depends(get_current_user),
    file: UploadFile = File(...),
    service: FileService = Depends(get_file_service),
) -> FileCreatedResponse:
    raw = await read_upload_with_limit(file)
    name, ct = validate_upload_body(original_filename=file.filename, body=raw)

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


@router.get(
    "",
    summary="Listar arquivos",
    description="Lista os metadados dos arquivos do utilizador autenticado (JWT Bearer).",
    response_model=list[FileResponse],
)
def list_files(
    current_user: User = Depends(get_current_user),
    service: FileService = Depends(get_file_service),
) -> list[FileResponse]:
    rows = service.list_for_user(current_user.id)
    return [
        FileResponse.model_validate(
            {
                **r.__dict__,
                "url": build_absolute_storage_url(r.stored_name),
            }
        )
        for r in rows
    ]


@router.get(
    "/download",
    summary="Baixar arquivo por chave",
    description="Descarrega o binário do arquivo. Requer JWT Bearer; a chave é a secretKey devolvida no envio.",
)
def download_file_by_key(
    key: str = Query(..., description="SecretKey retornada no upload."),
    current_user: User = Depends(get_current_user),
    service: FileService = Depends(get_file_service),
) -> Response:
    _file_meta_for_user_or_404(service, key, current_user.id)
    file_data = service.get_file_by_secret_key(key)
    if file_data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    original_name, _, content_type, data = file_data
    media_type = content_type or "application/octet-stream"
    encoded_name = quote(original_name)
    headers = {"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_name}"}
    return Response(content=data, media_type=media_type, headers=headers)


@router.get(
    "/key/{secretKey}",
    summary="Consultar arquivo por chave",
    description="Devolve id, URL e secretKey a partir da secretKey. Requer JWT Bearer.",
    response_model=FileCreatedResponse,
    response_model_by_alias=True,
)
def get_file_by_key(
    secretKey: str,
    current_user: User = Depends(get_current_user),
    service: FileService = Depends(get_file_service),
) -> FileCreatedResponse:
    row = _file_meta_for_user_or_404(service, secretKey, current_user.id)

    return FileCreatedResponse(
        id=row.id,
        url=build_absolute_storage_url(row.stored_name),
        secret_key=row.secret_key,
    )


@router.delete(
    "",
    summary="Eliminar arquivo por chave",
    description="Remove o arquivo associado à secretKey (query `key`). Requer JWT Bearer.",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_file_by_key(
    key: str = Query(..., description="SecretKey retornada no upload."),
    current_user: User = Depends(get_current_user),
    service: FileService = Depends(get_file_service),
) -> Response:
    _file_meta_for_user_or_404(service, key, current_user.id)
    deleted = service.delete_file_by_secret_key(key)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put(
    "/upload",
    summary="Atualizar arquivo por chave",
    description="Substitui o conteúdo do arquivo identificado pela secretKey (query `key`). Requer JWT Bearer.",
    response_model=FileCreatedResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_200_OK,
)
async def update_file_by_key(
    key: str = Query(..., description="SecretKey retornada no upload."),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    service: FileService = Depends(get_file_service),
) -> FileCreatedResponse:
    _file_meta_for_user_or_404(service, key, current_user.id)
    raw = await read_upload_with_limit(file)
    name, ct = validate_upload_body(original_filename=file.filename, body=raw)

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
