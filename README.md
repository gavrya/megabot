# megabot

A bot for the [Signal](https://signal.org) messenger. It connects to Signal through
[signal-cli-rest-api](https://github.com/bbernhard/signal-cli-rest-api), linked to an existing
Signal account as a secondary device (the same way Signal Desktop is linked), and exposes its
own FastAPI backend.

## Features

- Can be added to Signal groups
- Monitors group messages
- Sends messages to a group or directly to a user

## Tech Stack

- **Python 3.14** with **uv** for packages and Python versions
- **FastAPI** + **uvicorn**
- **Pydantic v2** + pydantic-settings
- **PostgreSQL 17** with **SQLAlchemy 2.0** (async, `asyncpg`)
- **Alembic** for migrations
- **signal-cli-rest-api** for the Signal connection
- **Ruff** for linting and formatting
- **Pyright** for static type checking
- **Docker** / Docker Compose (app, postgres, pgadmin, signal-api)

## Requirements

- [uv](https://docs.astral.sh/uv/) (installs Python 3.14 for you)
- [Docker](https://docs.docker.com/get-docker/) with Compose v2
- `make` (optional, for shortcuts)
- `qrencode`, for linking the Signal device
- A Signal account on a phone, to approve the device link

## Development

### Clone the Repository

```bash
git clone https://github.com/gavrya/megabot.git
cd megabot
```

### Setup

Install uv. It manages both Python and the project dependencies, so you don't need a
pre-installed Python:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh   # macOS / Linux
brew install uv                                   # or with Homebrew
```

Then install Python and the dependencies:

```bash
uv python install 3.14   # version pinned in .python-version
uv sync                  # creates .venv and installs all dependencies
```

Common uv commands:

```bash
uv sync                    # install dependencies from uv.lock
uv add <package>           # add a runtime dependency
uv add --dev <package>     # add a dev-only dependency
uv remove <package>        # remove a dependency
uv run <command>           # run a command inside the project's .venv
```

Install `qrencode`, used to render the QR code when linking the Signal device:

```bash
brew install qrencode            # macOS
sudo apt install qrencode        # Debian / Ubuntu
sudo dnf install qrencode        # Fedora / RHEL
sudo pacman -S qrencode          # Arch
```

### Configure Environment Variables

Copy `.env.example` to `.env` and configure the required variables.

```bash
cp .env.example .env
```

Variables are grouped by service prefix: `APP_`, `POSTGRES_`, `PGADMIN_`, `SIGNAL_API_`.
The database credentials are set twice (`POSTGRES_*` and `APP_DB_*`) and must match.

### Start the Application

Start the supporting services, apply migrations and run the API locally:

```bash
docker compose up -d postgres pgadmin signal-api   # start database, pgAdmin and Signal API
uv run alembic upgrade head                        # apply database migrations
uv run seed                                        # (optional) fill the database with seed data
uv run uvicorn app.main:app --reload               # run the API with autoreload
```

The API runs on <http://localhost:8000>.

Or run the full stack in Docker (migrations are applied on start):

```bash
docker compose up -d --build
```

#### Link the Signal device

1. On the phone, open **Signal → Settings → Linked devices → Link new device (+)**.
2. Run `./signal-api-link-device.sh` and scan the QR code right away (it expires in about a
   minute).
3. Check the result: `curl -s http://127.0.0.1:8080/v1/accounts`
   - `[]` means not linked yet.
   - `["+15551234567"]` means it's linked, with that number as the account ID.
   - `[""]` means a **phoneless** account is linked. It has no number, so use its account UUID
     wherever the API asks for a number. Get the UUID with:

     ```bash
     python3 -c "import json;print(json.load(open('signal-cli-data/data/accounts.json'))['accounts'][0]['uuid'])"
     ```

Account keys are stored in `./signal-cli-data/`. Keep this directory private.

### Database Migrations

Migrations live in `alembic/versions/`. The database must be running (`docker compose up -d postgres`).

#### Check status

```bash
uv run alembic current             # revision the database is at
uv run alembic heads               # latest revision in the code
uv run alembic history --verbose   # all revisions
```

If `current` and `heads` show the same revision, the database is up to date.

#### Create a migration

From the entities (`app/modules/<module>/entities/<module>_entity.py`). Alembic compares them
with the database and writes the difference:

```bash
uv run alembic revision --autogenerate -m "add x"   # or: make migration m="add x"
```

Manually, as an empty migration to fill in yourself (data changes, custom SQL):

```bash
uv run alembic revision -m "backfill x"
```

Always review the generated file in `alembic/versions/` before committing it. Autogenerate
doesn't detect every change.

#### Run migrations

```bash
uv run alembic upgrade head   # apply all pending migrations (make migrate)
uv run alembic downgrade -1   # roll back the last migration (make rollback)
```

Never edit a migration that has already been applied; create a new one instead.

### Database Seeds

Seeders fill the database with initial data. They live in `seeders/`, are named
`seed_<NNN>_<name>.py` and run in filename order. The database must be running and migrated.

#### Run seeders

```bash
uv run seed                  # run all seeders (make seed)
uv run seed --only <name>    # run only seeders whose filename contains <name>
```

In Docker, set `APP_RUN_SEEDS=true` in `.env` to run them on container start.

#### Create a seeder

Add a file `seeders/seed_<NNN>_<name>.py` with the next free number. It must expose
`async def run(session)`:

```python
from sqlalchemy.ext.asyncio import AsyncSession


async def run(session: AsyncSession) -> None: ...
```

Keep seeders idempotent: check before insert, so running them again doesn't create duplicates.
The runner commits after each seeder, so don't commit inside `run`.

### App API swagger docs

Interactive docs: <http://localhost:8000/docs>

### Signal API swagger docs

[signal-cli-rest-api](https://github.com/bbernhard/signal-cli-rest-api) is a REST wrapper
around `signal-cli`, a command-line Signal client. It runs as the `signal-api` Docker service,
is linked to your Signal account as a secondary device, and lets the bot send and receive
messages over plain HTTP. It listens only on `127.0.0.1:8080`.

- GitHub: <https://github.com/bbernhard/signal-cli-rest-api>
- Docker Hub: <https://hub.docker.com/r/bbernhard/signal-cli-rest-api>

Interactive docs: <http://127.0.0.1:8080/swagger/index.html> (available while the
`signal-api` container is running).

### Database web client

pgAdmin runs on <http://localhost:5050>. Log in with `PGADMIN_EMAIL` / `PGADMIN_PASSWORD`.
A `megabot` server is pre-registered, so you only enter the database password
(`POSTGRES_PASSWORD`). Inside pgAdmin the database host is `postgres`, not `localhost`.

### Code Quality

```bash
uv run ruff check .          # lint
uv run ruff check . --fix    # lint and autofix
uv run ruff format .         # format
uv run ruff format --check . # check formatting without writing (CI)
uv run pyright               # type check
```

Pyright is configured under `[tool.pyright]` in `pyproject.toml`. VS Code (Pylance) and
Antigravity (basedpyright) read the same section, so the editor reports the same errors as
the CLI.

### Make commands

| Command                  | Description                                 |
| ------------------------ | ------------------------------------------- |
| `make help`              | List all commands                           |
| `make install`           | Install dependencies (`uv sync`)            |
| `make run`               | Run the API with autoreload                 |
| `make lint`              | Lint the code                               |
| `make format`            | Format the code and apply safe fixes        |
| `make typecheck`         | Type-check the code with pyright            |
| `make check`             | Lint, format and type check, writes nothing |
| `make migration m="msg"` | Autogenerate a migration                    |
| `make migrate`           | Apply all pending migrations                |
| `make rollback`          | Roll back the last migration                |
| `make seed`              | Run all seeders                             |
| `make up`                | Start the full stack in Docker              |
| `make down`              | Stop the stack                              |
| `make logs`              | Tail the app logs                           |
