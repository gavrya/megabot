# AGENTS.md

**megabot** — async FastAPI service on PostgreSQL. This file is the single source of truth for
AI agents; `CLAUDE.md` and `ANTIGRAVITY.md` only import it. Edit rules here, nowhere else.

## Stack

Python 3.14 · uv · FastAPI · Pydantic v2 + pydantic-settings · SQLAlchemy 2.0 async (asyncpg)
· Alembic · PostgreSQL 17 · Ruff · Pyright (standard) · pytest + pytest-asyncio · Docker Compose
(`app`, `postgres`, `pgadmin`, `signal-api`).

## Commands

```bash
uv sync                                  # install (make install)
docker compose up -d postgres            # DB for local run + integration tests
uv run uvicorn app.main:app --reload     # API on :8000, docs at /docs (make run)
uv run pytest tests/unit                 # fast, needs nothing running (make test-unit)
uv run pytest                            # all tests (make test)
uv run alembic revision --autogenerate -m "msg"   # new migration (make migration m="msg")
uv run alembic upgrade head              # apply migrations (make migrate)
uv run seed                              # run seeders (make seed)
```

**Before finishing any change**, run and make green:

```bash
uv run ruff format . && uv run ruff check . --fix && uv run pyright && uv run pytest
```

## Architecture

Vertical-slice modules in `app/modules/<module>/`; infrastructure in `app/core/`; code used by
2+ modules in `app/shared/`. **Use `app/modules/articles/` as the reference module** — copy
its shape when adding a feature.

Flow is one-way, never skipping a layer:

```
controller -> service -> repository -> entity
           <- DTO (via mapper) <-
```

- **controllers/** — HTTP only: parse input, call one service, return a DTO. Relative paths;
  the module's `router.py` owns prefix and tags.
- **services/** — all business logic. Takes and returns DTOs, never entities. Raises
  `AppError` subclasses (`NotFoundError`, `ConflictError`), never `HTTPException`.
- **repositories/** — all queries; extend `BaseRepository[<X>Entity]`. `flush()` only, never
  `commit()` — the request-scoped session commits/rolls back.
- **mappers/** — the only place converting DTO <-> entity.
- **entities/** — `class XEntity(UuidPrimaryKeyMixin, TimestampMixin, Base)`; never redeclare `id`.
- **dtos/** — separate Create / Update / Response DTOs; never expose an entity over HTTP.
- **dependencies.py** exports `<Module>ServiceDep`; **router.py** is the module's public surface.

New module: also register its `router.py` in `app/router.py` (easy to forget — endpoints are
silently missing otherwise). Entities are autoloaded by `app/registry.py`.

## Conventions

- **One class per file**, file named `<subject>_<unit>.py` (`ArticleCreateDTO` →
  `dtos/article_create_dto.py`). Classes carry the layer suffix (`ArticleService`).
- **No `__init__.py` anywhere** (implicit namespace packages) — never add one.
- Modules never import another module's internals; go through its service.
- Everything touching the DB is `async`. Primary keys are `UUID`, never integers.
- Config only via `app/core/config.py` `Settings` — never `os.getenv`. Env vars are prefixed
  by compose service (`APP_`, `POSTGRES_`, `PGADMIN_`, `SIGNAL_API_`); document new ones in
  `.env.example`. A compose service interpolates only its own prefix.
- Log with `app.core.logging.get_logger(__name__)`, never `print`.
- Schema change → new Alembic migration. Never edit an applied migration.
- Dependencies via `uv add <pkg>` (`--dev` for dev); never hand-edit `pyproject.toml`.
- Comments only for a non-obvious "why".

## Tests

- `tests/unit/` (no DB) and `tests/integration/` (PostgreSQL, `megabot_test` DB) both mirror
  `app/`: `app/.../services/article_service.py` → `tests/unit/.../services/test_article_service.py`.
- Every change in `app/modules/` or `app/shared/` ships with tests at the mirrored path.
- Plain functions, no classes, no markers (added automatically), never import from `conftest.py`.
- Unit: mock repositories with `AsyncMock(spec=XRepository)`; hit controllers via `client`
  with `app.dependency_overrides[get_x_service]`. Integration: use `db_session` / `db_client`.

## Gotchas — intentional, do not "fix"

- Ruff `TC` rules stay disabled: on 3.14 they move imports into `TYPE_CHECKING` and FastAPI
  dependency injection breaks (every endpoint returns 422).
- `APP_DB_NAME=megabot_test` is forced by pytest-env so tests never hit the dev database.
- `docker-compose.yml` hardcodes `APP_DB_HOST: postgres` for the app container (`.env` has
  `localhost` for local runs).
- `README.md` must not be in `.dockerignore` — the hatchling build needs it.
- For DTOs with positional `Field(None, ...)` defaults, build them in tests with
  `Model.model_validate({...})` to keep Pyright happy.
- To assert a module router's paths, mount it on a fresh `FastAPI()` and read
  `app.openapi()["paths"]`.
