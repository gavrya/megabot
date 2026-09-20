# Project Instructions & Conventions

Master instruction file for **megabot** — the single source of truth for all AI coding
agents. `CLAUDE.md` and `ANTIGRAVITY.md` are thin wrappers that reference this file; do not
duplicate rules into them.

## Tech Stack

| Concern         | Choice                                        |
| --------------- | --------------------------------------------- |
| Language        | Python 3.12 (pinned in `.python-version`)     |
| Package manager | uv (`pyproject.toml` + `uv.lock`)             |
| Web framework   | FastAPI (ASGI, served by uvicorn)             |
| Validation      | Pydantic v2 + pydantic-settings               |
| Database        | PostgreSQL 17                                 |
| ORM             | SQLAlchemy 2.0, async, `asyncpg` driver       |
| Migrations      | Alembic (async env)                           |
| Lint + format   | Ruff (line length 100, target py312)          |
| Container       | Docker, `python:3.12-slim-bookworm` runtime   |
| Tests           | None — this project intentionally has no tests |

## Directory structure

**Module-based (vertical slices), one directory per unit type.** Each feature owns its full
stack; cross-cutting code lives in `core/` and `shared/`. Files carry their unit as a suffix
(`<module>_service.py`), so a filename is unambiguous anywhere in the repo.

```
megabot/
├── app/                                      # Application package
│   ├── core/                                 # Infrastructure configuration
│   │   ├── config.py                         # Typed settings loaded from the environment
│   │   ├── database.py                       # Async engine, session factory, request-scoped session
│   │   └── logging.py                        # Console/JSON formatters, request-id contextvar
│   │
│   ├── modules/                              # Domain / feature modules
│   │   ├── __init__.py                       # Registry: imports every module's entities for Alembic
│   │   └── <module>/                         # One directory per feature (vertical slice)
│   │       ├── controllers/                  # HTTP endpoints / handlers
│   │       │   └── <module>_controller.py    # Routes: read input, call a service, return a DTO
│   │       ├── dtos/                         # Module-specific Pydantic v2 schemas
│   │       │   ├── <module>_create_dto.py    # One DTO per file: create payload
│   │       │   ├── <module>_update_dto.py    # Update payload
│   │       │   └── <module>_response_dto.py  # Response shape
│   │       ├── entities/                     # SQLAlchemy ORM models
│   │       │   └── <module>_entity.py        # Table definition; extends Base
│   │       ├── mappers/                      # DTO <-> Entity converters
│   │       │   └── <module>_mapper.py        # to_entity / apply_update / to_dto
│   │       ├── repositories/                 # Database queries
│   │       │   └── <module>_repository.py    # Queries; extends BaseRepository
│   │       ├── services/                     # Business logic
│   │       │   └── <module>_service.py       # Orchestrates repository + mapper; raises AppError
│   │       ├── dependencies.py               # Module DI; exports <Module>ServiceDep
│   │       └── router.py                     # Module router export; owns the URL prefix and tags
│   │
│   ├── shared/                               # Cross-cutting concerns & base classes
│   │   ├── dtos/                             # Base DTOs & paginated responses
│   │   │   ├── page_params_dto.py            # PageParams (limit/offset query params)
│   │   │   ├── page_dto.py                   # Page[T] paginated envelope
│   │   │   └── error_response_dto.py         # ErrorResponse body
│   │   ├── entities/                         # Base ORM model
│   │   │   ├── base_entity.py                # DeclarativeBase + naming convention
│   │   │   ├── timestamp_mixin.py            # created_at / updated_at columns
│   │   │   └── uuid_primary_key_mixin.py     # UUID primary key (id)
│   │   ├── exceptions/                       # Custom domain errors & HTTP handlers
│   │   │   ├── app_error.py                  # AppError base class
│   │   │   ├── not_found_error.py            # NotFoundError (404)
│   │   │   ├── conflict_error.py             # ConflictError (409)
│   │   │   └── exception_handlers.py         # Maps raised errors to JSON error responses
│   │   ├── middlewares/                      # ASGI middleware
│   │   │   └── logging_middleware.py         # Request id, timing and access logging
│   │   ├── repositories/                     # Generic data access
│   │   │   └── base_repository.py            # Generic CRUD: get/list/count/add/update/delete
│   │   └── dependencies.py                   # Shared DI: SessionDep, PageParamsDep
│   │
│   ├── router.py                             # Aggregates every module router
│   └── main.py                               # App factory: middleware, handlers, lifespan
│
├── alembic/                                  # Migration environment
│   ├── versions/                             # Migration files, one per schema change
│   ├── env.py                                # Async migration runner; loads Base.metadata
│   └── script.py.mako                        # Template used for new migration files
│
├── seeders/                                  # Database seeding
│   ├── runner.py                             # Discovers and runs seeders in filename order
│   └── seed_<NNN>_<name>.py                  # One seeder; exposes async run(session)
│
├── .vscode/                                  # VS Code settings, extensions, launch configs, tasks
├── .antigravity/                             # Antigravity settings, extensions, rules
├── AGENTS.md                                 # Master instructions for AI agents (source of truth)
├── CLAUDE.md                                 # Claude Code wrapper -> AGENTS.md
├── ANTIGRAVITY.md                            # Antigravity wrapper -> AGENTS.md
├── Dockerfile                                # Multi-stage build: uv builder -> slim runtime
├── docker-compose.yml                        # app + postgres + adminer, driven by env vars
├── docker-entrypoint.sh                      # Runs migrations/seeds on start, then the CMD
├── alembic.ini                               # Alembic config: script location, file naming
├── Makefile                                  # Shortcuts for every command in this file
├── pyproject.toml                            # Dependencies + Ruff configuration
├── .env.example                              # Documented template for .env
└── .python-version                           # Python version pinned for uv
```

Rules for placement:

- **One definition per file.** A file in a unit directory declares exactly one class (or one
  router), named after the file: `article_create_dto.py` holds `ArticleCreateDTO` and nothing
  else. Never group related classes into a single module.
- Files are named `<subject>_<unit>.py`, where `<subject>` is the class name in snake_case
  minus the unit suffix. Adding a variant means adding a file, never widening an existing one.
- A controller file is one controller: its route handlers for that resource live together,
  since they share the router. Private helpers (leading underscore) stay beside the single
  public definition they serve.
- A module creates only the unit directories it needs: one without persistence has no
  `entities/`, `repositories/` or `mappers/`.
- Code belongs in `shared/` only when a second module would use it; otherwise keep it in the
  module.
- Modules must not import from each other's internals — go through the other module's service,
  imported from `app/modules/<other>/services/<other>_service.py`.
- Every module directory and every unit directory needs an `__init__.py`.

## Rules & Architecture

Inside a module the flow is one direction only, never skipping a step:

```
controller -> service -> repository -> entity
           <- DTO (via mapper) <-
```

### Rules per unit

- **`controllers/<module>_controller.py`** handles HTTP only: parse input, call one service,
  return a DTO. It never imports a repository, touches the ORM session, or holds business
  logic. Paths are relative — the module's `router.py` owns the prefix.
- **`services/<module>_service.py`** holds all business logic. It accepts and returns
  **DTOs**, never entities, and raises `AppError` subclasses (`NotFoundError`,
  `ConflictError`) rather than `HTTPException`.
- **`repositories/<module>_repository.py`** owns all queries. It `flush()`es but **never
  `commit()`s** — the request-scoped session in `app/core/database.py` commits on success and
  rolls back on error. Reusable query methods go in `shared/repositories/base_repository.py`.
- **`mappers/<module>_mapper.py`** is the only place converting DTO <-> Entity.
- **`entities/<module>_entity.py`** inherits `Base` from
  `app/shared/entities/base_entity.py`, its primary key from `UuidPrimaryKeyMixin` and its
  timestamps from `TimestampMixin`. Declare it as
  `class <Module>Entity(UuidPrimaryKeyMixin, TimestampMixin, Base)` and never redeclare `id`.
- **`dtos/<module>_dto.py`** holds the only types crossing the HTTP boundary. Separate
  Create/Update/Response models; never expose an entity directly.
- **`dependencies.py`** wires the repository into the service and exports `<Module>ServiceDep`.
- **`router.py`** is the module's public surface: it applies the prefix and tags, and is the
  only thing `app/router.py` imports.

### General rules

- Everything touching the database is `async`. No sync DB calls in request paths.
- **Primary keys are UUIDs**, never integers or sequences. The app generates one with
  `uuid4` on insert; the column also carries a `gen_random_uuid()` server default for rows
  inserted outside the ORM. Path parameters and service arguments are typed `UUID`.
- Configuration comes from `app/core/config.py` (pydantic-settings). Never call `os.getenv`;
  add a typed field to `Settings` and document it in `.env.example`.
- Log via `app.core.logging.get_logger(__name__)` — never `print`. Each request carries an
  `X-Request-ID` that is attached automatically to every log line.
- Errors are returned by the handlers in `app/shared/exceptions/exception_handlers.py` as
  `{"code", "message", "details?"}`. Add new failure modes as `AppError` subclasses.
- Any schema change requires an Alembic migration; never edit an applied migration.
- New module? Add one import line to `app/modules/__init__.py` (else Alembic autogenerate
  will emit a DROP for its table) and register its `router.py` in `app/router.py`.
- New dependency? `uv add <pkg>` (never edit `pyproject.toml` by hand) and commit `uv.lock`.
- Run `uv run ruff format . && uv run ruff check . --fix` before finishing a change.
- Do **not** write unit tests; verify changes by running the app against the local stack.

### Gotchas (verified, do not "fix" these)

- `docker-compose.yml` passes `DOCKER_POSTGRES_HOST`, **not** `POSTGRES_HOST`, to the app
  container. Compose auto-loads `.env`, where `POSTGRES_HOST=localhost` for local runs;
  passing it through would make the container dial its own loopback.
- `README.md` must stay out of `.dockerignore` — hatchling reads it for package metadata and
  the image build fails without it.
- `pyproject.toml` sets `runtime-evaluated-base-classes` for Ruff's TC rules so Pydantic and
  SQLAlchemy imports are never moved into a `TYPE_CHECKING` block, which breaks them at runtime.
- The runtime image is Debian slim, not Alpine, so dependencies without musl wheels still
  install as prebuilt wheels.
- `PGADMIN_EMAIL` must use a real TLD. pgAdmin rejects reserved domains such as `.local`
  and crash-loops on startup.
- pgAdmin reaches the database at host `postgres`, not `localhost` (which is its own container).

## CLI commands

All commands run from the repository root. Every `make` target maps to the `uv` command below it.

### Setup

```bash
cp .env.example .env    # first run only
uv sync                 # create .venv, install deps (make install)
```

### Run

```bash
uv run uvicorn app.main:app --reload     # local API on :8000 (make run)
docker compose up -d postgres pgadmin    # database + pgAdmin only
docker compose up -d --build             # full stack in Docker (make up)
docker compose down                      # stop (make down); add -v to wipe the DB volume
```

### Lint & format

```bash
uv run ruff check .            # lint (make lint)
uv run ruff format .           # format (make format also runs --fix)
uv run ruff check . --fix
uv run ruff format --check .   # CI, writes nothing (make check)
```

### Migrations

```bash
uv run alembic revision --autogenerate -m "msg"   # from entities (make migration m="msg")
uv run alembic revision -m "msg"                  # empty, hand-written
uv run alembic upgrade head                       # apply (make migrate)
uv run alembic downgrade -1                       # roll back one (make rollback)
uv run alembic current
uv run alembic history --verbose
```

### Seeds

```bash
uv run seed                   # run all seeders in filename order (make seed)
uv run seed --only <name>     # run matching seeders only
uv add <pkg>                  # add a dependency (--dev for dev-only)
```

## Other

### Endpoints

| Method | Path                    | Notes                             |
| ------ | ----------------------- | --------------------------------- |
| GET    | `/health`               | Includes DB liveness; never raises |
| GET    | `/api/v1/articles`      | `limit` (1-100, default 20), `offset` |
| POST   | `/api/v1/articles`      | 201                               |
| GET    | `/api/v1/articles/{uuid}` | 404 as `{"code":"not_found",...}` |
| PUT    | `/api/v1/articles/{uuid}` | Full replace                      |
| DELETE | `/api/v1/articles/{uuid}` | 204                               |

Docs at `/docs`, schema at `/openapi.json`.

### Conventions

- Files and modules: `snake_case`; classes: `PascalCase` with layer suffix
  (`ArticleService`, `ArticleRepository`, `ArticleMapper`, `ArticleEntity`, `ArticleCreateDTO`).
- Seeders are named `seed_<NNN>_<name>.py` and must be **idempotent** (check before insert).
- Comments only where the "why" is not obvious; no restating of code.
- `LOG_FORMAT=console` locally, `json` when deployed; `LOG_LEVEL` controls verbosity.

### Adding a new module (checklist)

Mirror an existing module; create only the unit directories the new module needs.

1. `app/modules/<module>/` with `__init__.py` in the module and in every unit directory
2. `entities/<module>_entity.py` — ORM model:
   `class <Module>Entity(UuidPrimaryKeyMixin, TimestampMixin, Base)`
3. Add `from app.modules.<module>.entities import <module>_entity` to `app/modules/__init__.py`
   and list it in `__all__`
4. `uv run alembic revision --autogenerate -m "create <module>"`, then review the generated file
5. `dtos/` — one file per DTO: `<module>_create_dto.py`, `<module>_update_dto.py`,
   `<module>_response_dto.py`
6. `mappers/<module>_mapper.py` — DTO <-> Entity
7. `repositories/<module>_repository.py` — subclass `BaseRepository[<Module>Entity]`
8. `services/<module>_service.py` — business logic raising `AppError` subclasses
9. `dependencies.py` — `<Module>ServiceDep`
10. `controllers/<module>_controller.py` — `APIRouter()` with relative paths
11. `router.py` — `router.include_router(<module>_controller.router, prefix="/<module>s", tags=[...])`
12. Register the module router in `app/router.py`
13. Optional `seeders/seed_NNN_<name>.py` (idempotent)
14. `uv run ruff format . && uv run ruff check . --fix`, then run the app and hit the endpoints

Steps 3 and 12 are the ones that get forgotten: without 3 Alembic will try to drop the new
table, without 12 the endpoints are simply absent. Note also that a controller route path of
`""` is only legal because `router.py` supplies a non-empty prefix — FastAPI rejects an empty
path and empty prefix together.

### Deployment

`docker-compose.yml` targets Coolify / Dokploy / Portainer: Compose v2 spec, no `version:`
key, every value driven by environment variables, `/health` used as the container healthcheck.
The app container runs migrations on start (`RUN_MIGRATIONS=true`) and optionally the seeders
(`RUN_SEEDS=true`). See the deployment section of `README.md`.
