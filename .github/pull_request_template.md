## What

<!-- What does this PR change? One or two sentences. -->

## Why

<!-- The problem or motivation. Link the issue if there is one: "Closes #123". -->

## How

<!-- Notable implementation decisions, trade-offs, or anything a reviewer should look at first. -->

## Type of change

- [ ] Feature
- [ ] Bug fix
- [ ] Refactor (no behaviour change)
- [ ] Infra / tooling / docs

## Checklist

- [ ] `make format && make check && make test` passes (integration tests need `docker compose up -d postgres`)
- [ ] Tests added/updated at the mirrored path in `tests/unit/` and/or `tests/integration/`
- [ ] Layering respected: controller → service → repository → entity; DTOs via mappers, no entities over HTTP
- [ ] New module's `router.py` registered in `app/router.py`
- [ ] Schema change has a new Alembic migration (no edits to applied migrations)
- [ ] New env vars added to `Settings` in `app/core/config.py` and documented in `.env.example`
- [ ] New dependencies added with `uv add` (no hand edits to `pyproject.toml`)
- [ ] `AGENTS.md` / `README.md` updated if conventions, commands, or setup changed

<!-- Tick only what applies; strike through or delete items that don't. -->

## How to test

<!-- Steps a reviewer can follow to verify the change, e.g. curl commands or /docs requests. -->

## Notes for deployment

<!-- Migrations to run, env vars to set, Signal API changes, breaking API changes. Delete if none. -->
