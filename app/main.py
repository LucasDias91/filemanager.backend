from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.files import router as files_router
from app.api.users import router as users_router
from app.db.database import init_db
from app.services.file_service import UPLOAD_ROOT

OPENAPI_TAGS = [
    {
        "name": "users",
        "description": "Criação e listagem de utilizadores.",
    },
    {
        "name": "files",
        "description": "Upload multipart (`user_id` + `file`) e listagem de metadados.",
    },
    {
        "name": "health",
        "description": "Estado do serviço.",
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

app.include_router(users_router)
app.include_router(files_router)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
