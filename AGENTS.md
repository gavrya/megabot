# Project Instructions & Conventions

Master instruction file for **megabot** — the single source of truth for all AI coding
agents. `CLAUDE.md` and `ANTIGRAVITY.md` are thin wrappers that reference this file; do not
duplicate rules into them.

## Tech Stack

| Concern         | Choice                                        |
| --------------- | --------------------------------------------- |
| Language        | Python 3.14 (pinned in `.python-version`)     |
| Package manager | uv (`pyproject.toml` + `uv.lock`)             |
| Web framework   | FastAPI (ASGI, served by uvicorn)             |
| Validation      | Pydantic v2 + pydantic-settings               |
| Database        | PostgreSQL 17                                 |
| ORM             | SQLAlchemy 2.0, async, `asyncpg` driver       |
| Migrations      | Alembic (async env)                           |
| Lint + format   | Ruff (line length 100, target py312)          |
| Type checking   | Pyright (`standard` mode, `[tool.pyright]`)   |
| Container       | Docker, `python:3.14-slim-bookworm` runtime   |
| Tests           | pytest + pytest-asyncio, httpx, pytest-cov    |

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
│   ├── registry.py                           # Entity autoloader: imports every entities/*_entity.py
│   ├── router.py                             # Aggregates every module router
│   └── main.py                               # App factory: middleware, handlers, lifespan
│
├── alembic/                                  # Migration environment
│   ├── versions/                             # Migration files, one per schema change
│   ├── env.py                                # Async migration runner; loads Base.metadata
│   └── script.py.mako                        # Template used for new migration files
│
├── tests/                                    # pytest suite (no __init__.py)
│   ├── conftest.py                           # app + client fixtures; unit/integration markers
│   ├── unit/                                 # No services needed; mirrors app/
│   │   ├── modules/<module>/<unit>/          # test_<subject>_<unit>.py per app file
│   │   └── shared/<unit>/
│   └── integration/                          # Needs PostgreSQL; mirrors app/
│       ├── conftest.py                       # db_engine, db_session, db_client fixtures
│       ├── modules/<module>/
│       └── shared/<unit>/
│
├── seeders/                                  # Database seeding
│   ├── runner.py                             # Discovers and runs seeders in filename order
│   └── seed_<NNN>_<name>.py                  # One seeder; exposes async run(session)
│
├── docker/                                   # Per-service container files
│   ├── app/
│   │   ├── Dockerfile                        # Multi-stage build: uv builder -> slim runtime
│   │   └── docker-entrypoint.sh              # Runs migrations/seeds on start, then the CMD
│   └── pgadmin/servers.json                  # Preconfigured pgAdmin server
├── .vscode/                                  # VS Code settings, extensions, launch configs, tasks
├── .antigravity/                             # Antigravity settings, extensions, rules
├── AGENTS.md                                 # Master instructions for AI agents (source of truth)
├── CLAUDE.md                                 # Claude Code wrapper -> AGENTS.md
├── ANTIGRAVITY.md                            # Antigravity wrapper -> AGENTS.md
├── docker-compose.yml                        # app + postgres + adminer, driven by env vars
├── alembic.ini                               # Alembic config: script location, file naming
├── Makefile                                  # Shortcuts for every command in this file
├── pyproject.toml                            # Dependencies + Ruff/Pyright config
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
- **No `__init__.py` anywhere.** Packages are implicit (PEP 420 namespace packages); never
  add one. `app/registry.py` autoloads entities by convention and needs no editing.

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
- Every env var is namespaced by the docker-compose service it belongs to: `APP_`,
  `POSTGRES_`, `PGADMIN_`, `SIGNAL_API_` (service `signal-api`). `Settings` uses
  `env_prefix="APP_"`, so field `db_host` reads `APP_DB_HOST`. Each namespace gets its own
  banner comment block in `.env.example`. In `docker-compose.yml` a service may interpolate
  only variables with its own prefix — never `${POSTGRES_USER}` inside `app`, and no
  cross-prefix references (`APP_DB_USER=${POSTGRES_USER}`) in `.env` either. Shared values
  such as the DB credentials are therefore set twice (`POSTGRES_USER` and `APP_DB_USER`)
  and must be kept in sync by hand.
- Log via `app.core.logging.get_logger(__name__)` — never `print`. Each request carries an
  `X-Request-ID` that is attached automatically to every log line.
- Errors are returned by the handlers in `app/shared/exceptions/exception_handlers.py` as
  `{"code", "message", "details?"}`. Add new failure modes as `AppError` subclasses.
- Any schema change requires an Alembic migration; never edit an applied migration.
- New module? Register its `router.py` in `app/router.py`. Entities need no registration:
  `app/registry.py` imports every `**/entities/*_entity.py` under `app/` before autogenerate
  runs — module and shared entities alike. The `entities/` directory plus the `_entity.py`
  suffix is what makes a table visible to Alembic.
- New dependency? `uv add <pkg>` (never edit `pyproject.toml` by hand) and commit `uv.lock`.
- Run `uv run ruff format . && uv run ruff check . --fix && uv run pyright && uv run pytest`
  before finishing a change; pyright must report 0 errors and every test must pass.
- Every change to `app/modules/` or `app/shared/` comes with tests in `tests/`, at the
  mirrored path (see **Tests** below).

### Tests

- Two suites, by directory: `tests/unit/` and `tests/integration/`. Each mirrors `app/`:
  `app/modules/articles/services/article_service.py` is unit-tested by
  `tests/unit/modules/articles/services/test_article_service.py`. A test that touches the
  database goes in `tests/integration/`, never in `tests/unit/`; if a file covers both, split
  it into two files with the same name, one per suite.
- No `__init__.py` here either; pytest runs with `--import-mode=importlib`, which allows the
  same filename in both suites. Module-level files get the module name
  (`test_article_router.py`, not `test_router.py`).
- `tests/conftest.py` marks every test `unit` or `integration` from its directory; don't add
  these markers by hand.
- Plain functions, no test classes. `asyncio_mode = "auto"`, so async tests need no marker.
- **Unit tests** (no database): services get `AsyncMock(spec=<Module>Repository)`;
  controllers are hit through `client` with the service replaced by
  `app.dependency_overrides[get_<module>_service] = lambda: mock`.
- **Integration tests** use the `db_engine`, `db_session` or `db_client` fixtures from
  `tests/integration/conftest.py` (unavailable to unit tests) and run against the
  `megabot_test` database (created on demand, schema rebuilt via `Base.metadata.create_all`
  each run, one rolled-back transaction per test). Needs `docker compose up -d postgres`;
  skipped when unreachable.
- Never import from `conftest.py`; share setup through fixtures. Per-file helpers stay
  private (leading underscore) in the test file.

### Gotchas (verified, do not "fix" these)

- `docker-compose.yml` hardcodes `APP_DB_HOST: postgres` / `APP_DB_PORT: 5432` for the app
  container instead of interpolating `${APP_DB_HOST}`. Compose auto-loads `.env`, where
  `APP_DB_HOST=localhost` for local runs; passing it through would make the container dial
  its own loopback.
- `README.md` must stay out of `.dockerignore` — hatchling reads it for package metadata and
  the image build fails without it.
- Ruff's `TC` (flake8-type-checking) rules are deliberately **not** enabled. On Python 3.14 they
  move imports into `TYPE_CHECKING` blocks; the app still imports and starts, but FastAPI can no
  longer resolve `<Module>ServiceDep` and every endpoint answers 422 `Field required`.
- `pyproject.toml` sets `src = ["."]` so Ruff treats the project root as the import root.
  Pointing `src` at the packages themselves makes isort sort `app` and `seeders` as third-party.
- The runtime image is Debian slim, not Alpine, so dependencies without musl wheels still
  install as prebuilt wheels.
- `PGADMIN_EMAIL` must use a real TLD. pgAdmin rejects reserved domains such as `.local`
  and crash-loops on startup.
- pgAdmin reaches the database at host `postgres`, not `localhost` (which is its own container).
- `APP_DB_NAME=megabot_test` is forced by pytest-env in `[tool.pytest.ini_options]`, so it wins
  over `.env` and the shell. This is what keeps a test run (which drops and recreates every
  table) away from the development database — never weaken it to a default.
- Pyright doesn't treat a positional default (`Field(None, min_length=1)`) as optional, so in
  tests build such DTOs with `Model.model_validate({...})` rather than keyword arguments.
- `APIRouter.routes` of a module router holds lazy included routers on current FastAPI, not
  `APIRoute`s. To assert on a module's paths, mount it on a fresh `FastAPI()` and read
  `app.openapi()["paths"]`.

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

### Tests

```bash
uv run pytest                           # all tests (make test)
uv run pytest tests/unit                # unit tests, nothing running (make test-unit)
uv run pytest tests/integration         # needs postgres up (make test-integration)
uv run pytest --cov --cov-report=term   # with coverage (make test-cov)
```

### Lint, format & type check

```bash
uv run ruff check .            # lint (make lint)
uv run ruff format .           # format (make format also runs --fix)
uv run ruff check . --fix
uv run ruff format --check .   # CI, writes nothing (make check also runs pyright)
uv run pyright                 # type check (make typecheck)
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
- `APP_LOG_FORMAT=console` locally, `json` when deployed; `APP_LOG_LEVEL` controls verbosity.

### Adding a new module (checklist)

Mirror an existing module; create only the unit directories the new module needs.

1. `app/modules/<module>/` with its unit directories (no `__init__.py` files)
2. `entities/<module>_entity.py` — ORM model:
   `class <Module>Entity(UuidPrimaryKeyMixin, TimestampMixin, Base)`.
   It is autoloaded, provided it sits in an `entities/` directory and ends in `_entity.py`
3. `uv run alembic revision --autogenerate -m "create <module>"`, then review the generated file
4. `dtos/` — one file per DTO: `<module>_create_dto.py`, `<module>_update_dto.py`,
   `<module>_response_dto.py`
5. `mappers/<module>_mapper.py` — DTO <-> Entity
6. `repositories/<module>_repository.py` — subclass `BaseRepository[<Module>Entity]`
7. `services/<module>_service.py` — business logic raising `AppError` subclasses
8. `dependencies.py` — `<Module>ServiceDep`
9. `controllers/<module>_controller.py` — `APIRouter()` with relative paths
10. `router.py` — `router.include_router(<module>_controller.router, prefix="/<module>s", tags=[...])`
11. Register the module router in `app/router.py`
12. Optional `seeders/seed_NNN_<module>.py` (idempotent)
13. Unit tests under `tests/unit/modules/<module>/`, mirroring the module's files: DTOs,
    mapper, entity, service (mocked repository), controller (mocked service), dependencies,
    router. Integration tests under `tests/integration/modules/<module>/`: repository and an
    end-to-end `test_<module>s_api.py` using `db_client`
14. `uv run ruff format . && uv run ruff check . --fix && uv run pyright && uv run pytest`

Step 11 is the one that gets forgotten — without it the endpoints are simply absent. Entity
registration is automatic, but only for files named `*_entity.py` inside an `entities/`
directory anywhere under `app/`. Note also that a controller route path of
`""` is only legal because `router.py` supplies a non-empty prefix — FastAPI rejects an empty
path and empty prefix together.

### Deployment

`docker-compose.yml` targets Coolify / Dokploy / Portainer: Compose v2 spec, no `version:`
key, every value driven by environment variables, `/health` used as the container healthcheck.
The app container runs migrations on start (`APP_RUN_MIGRATIONS=true`) and optionally the
seeders (`APP_RUN_SEEDS=true`). See the deployment section of `README.md`.
