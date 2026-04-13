from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from app.api.auth import router as auth_router
from app.api.files import router as files_router
from app.api.users import router as users_router
from app.db.database import init_db
from app.services.file_service import UPLOAD_ROOT

OPENAPI_TAGS = [
    {
        "name": "auth",
        "description": "Autenticação (login) para obter token JWT Bearer.",
    },
    {
        "name": "users",
        "description": "Criação de utilizadores; listagem com JWT Bearer.",
    },
    {
        "name": "files",
        "description": (
            "Todas as rotas /api/files/* exigem JWT Bearer. "
            "Listagem e operações por chave aplicam-se apenas aos arquivos do utilizador do token. "
            "Envio multipart via FormData com o campo `file`; o utilizador vem do token. "
            "O POST /api/files/upload devolve id, URL em /storage/{stored_name} e secretKey. "
            "O GET /storage/{stored_name} serve o arquivo (StaticFiles)."
        ),
    },
]


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title="[FileManager Backend]",
    description=(
        "API para gestão de arquivos. Autenticação via JWT Bearer."
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
app.include_router(files_router, prefix="/api")

UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
app.mount(
    "/storage",
    StaticFiles(directory=str(UPLOAD_ROOT), html=False),
    name="storage",
)
