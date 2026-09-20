# megabot

Minimal, modern FastAPI service: async SQLAlchemy 2.0 + PostgreSQL, Alembic migrations,
seeders, Pydantic v2 DTOs and a module-based (vertical slice) architecture.

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
│   │   │   └── timestamp_mixin.py            # created_at / updated_at columns
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
├── Makefile                                  # Shortcuts for the commands below
├── pyproject.toml                            # Dependencies + Ruff configuration
├── .env.example                              # Documented template for .env
└── .python-version                           # Python version pinned for uv
```

Each file declares exactly one class, named after the file — `article_create_dto.py` holds
`ArticleCreateDTO` and nothing else. A module creates only the unit directories it needs: one
without persistence has no `entities/`, `repositories/` or `mappers/`.

Each feature is self-contained: adding one means adding a directory under `app/modules/`,
not touching shared layer directories. Inside a module the flow is
`controller -> service -> repository -> entity`, with the mapper converting entities to DTOs.
Controllers never touch the ORM, services never return entities, repositories never commit.

## Endpoints

| Method | Path                     | Description                       |
| ------ | ------------------------ | --------------------------------- |
| GET    | `/health`                | Health check (incl. DB liveness)   |
| GET    | `/api/v1/articles`       | List articles (`limit`, `offset`)  |
| POST   | `/api/v1/articles`       | Create an article                  |
| GET    | `/api/v1/articles/{id}`  | Get one article                    |
| PUT    | `/api/v1/articles/{id}`  | Update an article                  |
| DELETE | `/api/v1/articles/{id}`  | Delete an article                  |

Interactive docs: <http://localhost:8000/docs>

---

## 1. Prepare the local environment

### Install uv

`uv` manages both Python itself and the project dependencies — you do not need a
pre-installed Python.

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

```bash
# macOS (Homebrew)
brew install uv
```

```powershell
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Install Python

The version is pinned in `.python-version`:

```bash
uv python install 3.12
```

### Other tools

- **Docker** (with Compose v2) — for PostgreSQL and pgAdmin: <https://docs.docker.com/get-docker/>
- **make** (optional) — shortcuts for every command below; preinstalled on macOS/Linux.
- **Ruff** is installed as a dev dependency, no separate install needed.

## 2. Install packages

```bash
uv sync
```

This creates `.venv/`, installs runtime + dev dependencies and writes `uv.lock`.

Add a package later:

```bash
uv add <package>          # runtime dependency
uv add --dev <package>    # dev-only dependency
```

## 3. Configure and run

```bash
cp .env.example .env
```

Start PostgreSQL and pgAdmin (<http://localhost:5050>):

```bash
docker compose up -d postgres pgadmin
```

Apply migrations, then run the API:

```bash
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

The API is on <http://localhost:8000>, docs on <http://localhost:8000/docs>.

### Run everything in Docker

```bash
docker compose up -d --build
```

The app container applies migrations on start (`RUN_MIGRATIONS=true`) and can also run the
seeders (`RUN_SEEDS=true`).

| Service  | URL                                              | Credentials                            |
| -------- | ------------------------------------------------ | -------------------------------------- |
| API      | <http://localhost:8000> (docs at `/docs`)        | —                                      |
| pgAdmin  | <http://localhost:5050>                          | `PGADMIN_EMAIL` / `PGADMIN_PASSWORD`   |

### Connecting a database UI

pgAdmin runs **inside a container**, so the database host is the compose service name
`postgres` — never `localhost`, which refers to pgAdmin's own container and fails with
`connection refused`.

| Field    | Value                              |
| -------- | ---------------------------------- |
| System   | PostgreSQL                         |
| Server   | `postgres`                         |
| Username | `POSTGRES_USER` (default `megabot`)   |
| Password | `POSTGRES_PASSWORD` (default `megabot`) |
| Database | `POSTGRES_DB` (default `megabot`)     |

pgAdmin ships a pre-registered `megabot` server from `docker/pgadmin/servers.json`, so in
practice you only enter the database password when expanding it. From your own machine
(psql, TablePlus, DataGrip) use `localhost:5432` instead — the port is published.

### Lint and format

```bash
uv run ruff check .          # lint
uv run ruff check . --fix    # lint + autofix
uv run ruff format .         # format
```

With make: `make lint`, `make format`, `make check` (CI-safe, writes nothing).

## 4. Migrations

Migrations live in `alembic/versions/` and are generated against the entities declared in
each module (`app/modules/<module>/entities/<module>_entity.py`).

```bash
# Autogenerate from the entities (diff of models vs. database)
uv run alembic revision --autogenerate -m "add published flag"

# Create an empty migration to write by hand
uv run alembic revision -m "backfill article slugs"

# Apply everything pending
uv run alembic upgrade head

# Roll back the last migration / go to a specific revision
uv run alembic downgrade -1
uv run alembic downgrade 0001_articles

# Inspect
uv run alembic current
uv run alembic history --verbose
```

Always review an autogenerated migration before committing it — Alembic detects most, but
not all, changes.

> New module? Import its entity in `app/modules/__init__.py`, otherwise autogenerate will not
> see the table — and will generate a `DROP` for it.

## 5. Seeds

Seeders are plain modules in `seeders/`, named `seed_<NNN>_<name>.py` and exposing
`async def run(session: AsyncSession) -> None`. The runner executes them in filename order
and commits after each one.

```bash
uv run seed                  # run all seeders
uv run seed --only <name>    # run only seeders whose filename contains <name>
```

Create a new seeder:

```bash
cat > seeders/seed_002_tags.py <<'EOF'
from sqlalchemy.ext.asyncio import AsyncSession


async def run(session: AsyncSession) -> None:
    ...
EOF
```

Keep seeders idempotent (check before insert) so they can be re-run safely.

## Make targets

```bash
make help       # list all targets
make install    # uv sync
make run        # uvicorn with reload
make lint       # ruff check
make format     # ruff format + fix
make migration m="add x"   # autogenerate a migration
make migrate    # alembic upgrade head
make rollback   # alembic downgrade -1
make seed       # run seeders
make up/down/logs          # docker compose
```

## Deployment (Coolify / Dokploy / Portainer)

`docker-compose.yml` is plain Compose v2 with no `version:` key and every value driven by
environment variables, so it can be imported as-is:

1. Create a new **Docker Compose** resource pointing at this repository.
2. Paste the variables from `.env.example` into the platform's environment editor —
   at minimum `POSTGRES_PASSWORD`, `APP_ENV=production`, `LOG_FORMAT=json`.
3. Leave `DOCKER_POSTGRES_HOST=postgres` so the app reaches the database over the compose
   network. (`POSTGRES_HOST` is only the host used when running the app outside Docker;
   compose deliberately does not pass it to the container.)
4. Let the platform's proxy route to the `app` service on container port `8000`; remove or
   ignore the `ports:` mappings if you do not want the ports published on the host.
5. The `app` service has a `/health` healthcheck the platform uses for zero-downtime deploys.

## IDE setup

- **VS Code** — `.vscode/` ships settings, recommended extensions, launch configs
  (uvicorn with debugger, seed runner) and tasks. Open the folder and accept the extension
  recommendations; Ruff formats on save and fixes imports.
- **Google Antigravity** — `.antigravity/` mirrors those settings. Antigravity is
  VS Code-based, so `.vscode/` applies as well.

Both expect the interpreter at `.venv/bin/python` (created by `uv sync`).

## AI agent instructions

`AGENTS.md` in the repository root is the single source of truth: tech stack, directory
layout, architecture rules, CLI commands and conventions. Everything else is a thin wrapper
pointing at it, so rules are never duplicated:

| File                           | Tool                  | Contents            |
| ------------------------------ | --------------------- | ------------------- |
| `AGENTS.md`                    | Shared standard       | The actual rules    |
| `CLAUDE.md`                    | Claude Code           | `@AGENTS.md` import |
| `ANTIGRAVITY.md`               | Google Antigravity    | Link to `AGENTS.md` |
| `.antigravity/rules/project.md`| Antigravity workspace | Link to `AGENTS.md` |

Update `AGENTS.md` only — the wrappers never need to change.

## Logging

Configured in `app/core/logging.py` and `app/shared/middlewares/logging_middleware.py`. `LOG_FORMAT=console` gives readable local output,
`LOG_FORMAT=json` structured logs for production. Every request gets an `X-Request-ID`
(generated or taken from the incoming header) that is attached to each log line and
returned in the response.
