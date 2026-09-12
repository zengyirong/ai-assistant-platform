# Backend — AI Assistant Platform

FastAPI scaffold aligned with Phase 0.

## Layout

```text
app/
  api/          # HTTP routes (/health, /ready, /api/v1/*)
  core/         # config, errors, logging, middleware
  db/           # SQLAlchemy async engine
  schemas/      # Pydantic (incl. SSE V1)
  models/       # ORM (Phase 1)
  modules/      # application services (Phase 1)
  ai/           # LLM / Embedding / VectorStore interfaces
  domains/      # hospital / hr placeholders
alembic/        # migrations (models first, then autogenerate)
tests/
```

## Setup

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
pip install -e ".[dev]"
cp ../.env.example ../.env
```

Start MySQL + Qdrant:

```bash
docker compose -f ../deploy/docker-compose.yml up -d
```

Run API:

```bash
uvicorn app.main:app --reload --app-dir .
# or from backend/:
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Checks:

```bash
curl http://127.0.0.1:8000/health
pytest
ruff check .
```

## Notes

- Schema bootstrap: Compose applies `docs/mysql/ddl_v1.sql` + seed on first MySQL start.
- Alembic is prepared; create SQLAlchemy models before `alembic revision --autogenerate`.
- Auth endpoints are stubs until Phase 1 Auth module.
