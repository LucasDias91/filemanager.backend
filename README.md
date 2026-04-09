# FileManager — Backend

API REST em **FastAPI** com SQLite (SQLAlchemy), JWT para autenticação e upload de arquivos com validação de tipo e tamanho.

## Como iniciar a aplicação (stack completo)

1. **Backend (esta pasta)** — instale as dependências (uma vez) e suba a API na porta **8000** (veja [Executar o backend](#executar-o-backend) abaixo).
2. **Frontend** — na pasta `filemanager.frontend`, no Windows, execute **`start.bat`**: ele sobe o site na porta **5500** e abre o navegador. Em outros sistemas, use `python -m http.server 5500` na pasta do frontend (detalhes no README do frontend).

Ordem: sempre deixe o backend rodando antes de usar o frontend.

## Requisitos

- Python 3.10+ (recomendado 3.11+)
- Ambiente virtual (recomendado)

## Instalação

Na pasta do backend:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

No Linux/macOS, ative com `source .venv/bin/activate`.

## Executar o backend

A partir da raiz do backend (onde fica a pasta `app/`):

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- **Swagger UI:** http://127.0.0.1:8000/swagger  
- **ReDoc:** http://127.0.0.1:8000/redoc  

Na primeira execução o SQLite é criado automaticamente (`filemanager.db` no diretório de trabalho atual).

## Variáveis de ambiente (opcional)

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `FILEMANAGER_STORAGE_PATH` | Pasta onde os uploads são gravados | `C:\fileManager\storage` |
| `PUBLIC_BASE_URL` | Base das URLs públicas dos arquivos (`/storage/...`) | `http://127.0.0.1:8000` |

Ajuste `PUBLIC_BASE_URL` se a API for acessada por outro host ou porta (para os links retornados no JSON baterem com o acesso real).

## Endpoints (resumo)

| Prefixo | Uso |
|---------|-----|
| `POST /api/auth/login` | Login (JSON: `username`, `password`) → token JWT |
| `POST /api/users` | Criar usuário (público no MVP) |
| `GET /api/users` | Listar usuários (Bearer JWT) |
| `POST /api/files/upload` | Upload multipart, campo `file` (Bearer JWT) |
| `GET /api/files` | Listar metadados dos arquivos (Bearer JWT) |
| `GET /storage/{nome}` | Download do arquivo enviado (servido como estático) |

CORS está liberado para qualquer origem (`*`), adequado para desenvolvimento local com frontend em outra porta.

## Estrutura do projeto

Camadas: rotas (`app/api/`) → serviços (`app/services/`) → repositórios (`app/repositories/`), modelos e schemas em `app/models/` e `app/schemas/`.

## Frontend

O cliente web fica no repositório/pasta **filemanager.frontend**. Configure a URL da API em `js/config.js` (`API_BASE_URL`) para apontar para este servidor (por padrão `http://127.0.0.1:8000`).
