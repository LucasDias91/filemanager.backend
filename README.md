# FileManager — Backend

API REST em **FastAPI** com SQLite (SQLAlchemy), JWT para autenticação e upload de ficheiros (validação de extensão/conteúdo e limite de tamanho).

## Início rápido com `start.bat` (Windows)

Na pasta deste projeto (`filemanager.backend`), execute **`start.bat`**. O script tenta localizar o Python, cria `.venv` se necessário, instala `requirements.txt` e arranca o Uvicorn em **http://127.0.0.1:8000** (abre o Swagger após alguns segundos).

## Se o `start.bat` não funcionar (execução manual)

Use estes passos em qualquer sistema, sempre **a partir desta pasta** (onde existem `app/` e `requirements.txt`).

1. **Python 3.10+** instalado e acessível no terminal (`python` ou `py`).

2. **Ambiente virtual e dependências:**

   ```bash
   python -m venv .venv
   ```

   Ative o ambiente:

   - **Windows (cmd/PowerShell):** `.venv\Scripts\activate`
   - **Linux / macOS:** `source .venv/bin/activate`

   Depois:

   ```bash
   pip install -r requirements.txt
   ```

3. **Arrancar a API** (o diretório de trabalho atual deve ser a raiz do backend):

   ```bash
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

4. **Documentação interativa**

   - Swagger: http://127.0.0.1:8000/swagger  
   - ReDoc: http://127.0.0.1:8000/redoc  

Na primeira execução o SQLite é criado automaticamente (`filemanager.db` na pasta de onde corre o comando).

## Requisitos

- Python 3.10+ (recomendado 3.11+)
- Ambiente virtual (recomendado; o `start.bat` cria `.venv`)

## Variáveis de ambiente (opcional)

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `FILEMANAGER_STORAGE_PATH` | Pasta onde os uploads são gravados | `C:\fileManager\storage` |
| `PUBLIC_BASE_URL` | Base das URLs públicas dos ficheiros (`/storage/...`) | `http://127.0.0.1:8000` |

Ajuste `PUBLIC_BASE_URL` se a API for acedida por outro host ou porta (para os links no JSON coincidirem com o acesso real).

## Endpoints (resumo)

| Prefixo | Uso |
|---------|-----|
| `POST /api/auth/login` | Login (JSON: `username`, `password`) → token JWT |
| `POST /api/users` | Criar utilizador (público no MVP) |
| `GET /api/users` | Listar utilizadores (Bearer JWT) |
| `POST /api/files/upload` | Upload multipart, campo `file` (Bearer JWT) |
| `GET /api/files` | Listar metadados (Bearer JWT) |
| `GET /storage/{nome}` | Ficheiro gravado (servido como estático) |

CORS está configurado para desenvolvimento (`allow_origins=["*"]`).

## Estrutura do projeto

Camadas: rotas (`app/api/`) → serviços (`app/services/`) → repositórios (`app/repositories/`), modelos e schemas em `app/models/` e `app/schemas/`.

O cliente web do mesmo repositório vive na pasta **`filemanager.frontend`**; consulte o README dessa pasta apenas para o frontend.
