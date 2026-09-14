# Backend — AI Assistant Platform

FastAPI backend for knowledge base + RAG chat (Phase 0 / M1–M3).

## Layout

```text
app/
  api/          # HTTP routes (/health, /ready, /api/v1/*)
  core/         # config, errors, logging, middleware
  db/           # SQLAlchemy async engine
  schemas/      # Pydantic (incl. SSE V1)
  models/       # ORM
  modules/      # application services
  ai/           # LLM / Embedding / VectorStore / parsers
  domains/      # hospital / hr placeholders
alembic/        # schema migrations (source of truth for new envs)
tests/          # unit + API smoke (+ rag_eval golden smoke)
```

## Setup

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
pip install -e ".[dev]"
cp ../.env.example ../.env
# Edit ../.env: MYSQL_PASSWORD, and optionally real LLM/Embedding keys
```

Dependencies (MySQL on host by default; Qdrant via Compose):

```bash
docker compose -f ../deploy/docker-compose.yml up -d
```

### Database: Alembic first

**New empty database** (create schema `ai_assistant` first):

```bash
# MySQL: CREATE DATABASE ai_assistant ...;
cd backend
alembic upgrade head
mysql -h 127.0.0.1 -u root -p ai_assistant < ../docs/mysql/seed_v1.sql
```

**Existing database** already created from `docs/mysql/ddl_v1.sql`:

```bash
# Mark baseline without re-creating tables
alembic stamp 20260914_0001
# Apply later revisions (e.g. citation ON DELETE CASCADE)
alembic upgrade head
```

If the DB was rebuilt from the latest DDL (already includes citation CASCADE), you may `alembic stamp head` instead.

`docs/mysql/ddl_v1.sql` remains a readable reference / Docker MySQL init fallback — **prefer Alembic for new environments**.

### Run API

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Checks:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/ready
```

`/ready` probes MySQL + Qdrant. Local demo: start Qdrant via Compose; MySQL must accept credentials from `.env`.

### Tests & lint

Providers are forced to **fake** in `tests/conftest.py` so pytest never calls paid APIs even if `.env` has real keys.

```bash
cd backend
ruff check .
pytest                 # needs MySQL + seed + Qdrant for API tests
pytest tests/unit tests/rag_eval -q   # no MySQL required
```

CI (GitHub Actions): `.github/workflows/backend-ci.yml` runs ruff + Alembic + seed + pytest with MySQL/Qdrant services and `LLM_PROVIDER=fake` / `EMBEDDING_PROVIDER=fake`.

### .env notes

| Variable | Notes |
|---|---|
| `LLM_PROVIDER` / `EMBEDDING_PROVIDER` | Default `fake` for offline; `openai_compatible` for real APIs |
| `EMBEDDING_DIMENSION` | Must match Qdrant collection; changing dim → new `QDRANT_COLLECTION` + re-index |
| `EMBEDDING_BATCH_SIZE` | Aliyun DashScope v3/v4 max **10** |
| `QDRANT_URL` | On Windows, system HTTP proxy can break local Qdrant — clients use `trust_env=False` |
| Secrets | Keep `.env` out of git; restart uvicorn fully after provider/dim changes |

Demo logins (after seed):

| User | Password | Role |
|---|---|---|
| `admin` | `Admin@123456` | ADMIN |
| `demo` | `Demo@123456` | USER |

ADMIN may also create more same-org USER accounts via `POST /api/v1/users` (see `docs/api.md` §4.1.1).
