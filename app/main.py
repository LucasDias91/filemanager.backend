from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from app.api.auth import router as auth_router
from app.api.files import public_router as files_public_router, router as files_router
from app.api.users import router as users_router
from app.db.database import init_db
from app.services.file_service import UPLOAD_ROOT

OPENAPI_TAGS = [
    {
        "name": "auth",
        "description": "Autenticação pública (login) para obter token JWT Bearer.",
    },
    {
        "name": "users",
        "description": "Criação e listagem de utilizadores (requer JWT Bearer).",
    },
    {
        "name": "files",
        "description": (
            "Multipart upload via FormData with field `file` (JWT Bearer); user from token. "
            "POST /api/files/upload returns id, URL under /storage/{stored_name}, and secretKey. "
            "GET /storage/{stored_name} serves the file (StaticFiles). "
            "Metadata listing requires JWT Bearer."
        ),
    },
]


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title="filemanager.backend",
    description=(
        "API REST em camadas (rotas → serviços → repositórios) com SQLite e SQLAlchemy. "
        "Experimente os endpoints abaixo diretamente no Swagger."
    ),
    version="0.1.0",
    lifespan=lifespan,
    openapi_tags=OPENAPI_TAGS,
    docs_url="/swagger",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(files_public_router, prefix="/api")
app.include_router(files_router, prefix="/api")

UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
app.mount(
    "/storage",
    StaticFiles(directory=str(UPLOAD_ROOT), html=False),
    name="storage",
)
