"""Database fixtures for integration tests.

They run against the PostgreSQL database named by `APP_DB_NAME`, which pytest-env forces to
`megabot_test` (see `[tool.pytest.ini_options]`). The database is created when missing, its
schema is rebuilt from the entities once per run, and every test runs inside a transaction
that is rolled back afterwards. When the server is unreachable, every test here is skipped.
"""

from collections.abc import AsyncGenerator

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy import make_url, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine

from app.core.config import settings
from app.core.database import engine as app_engine
from app.core.database import get_session
from app.registry import import_entity_modules
from app.shared.entities.base_entity import Base


async def _ensure_database_exists() -> None:
    url = make_url(str(settings.database_url))
    admin_engine = create_async_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    try:
        async with admin_engine.connect() as connection:
            exists = await connection.scalar(
                text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": url.database}
            )
            if not exists:
                await connection.execute(text(f'CREATE DATABASE "{url.database}"'))
    finally:
        await admin_engine.dispose()


@pytest.fixture(scope="session")
async def db_engine() -> AsyncGenerator[AsyncEngine]:
    try:
        await _ensure_database_exists()
    except Exception as exc:
        pytest.skip(f"PostgreSQL test database unreachable ({settings.db_host}): {exc}")

    import_entity_modules()
    async with app_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    yield app_engine
    async with app_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
    await app_engine.dispose()


@pytest.fixture
async def db_session(db_engine: AsyncEngine) -> AsyncGenerator[AsyncSession]:
    async with db_engine.connect() as connection:
        transaction = await connection.begin()
        # Commits inside the code under test only release a savepoint; the outer transaction
        # is rolled back, so tests never see each other's rows.
        session = AsyncSession(
            bind=connection,
            expire_on_commit=False,
            autoflush=False,
            join_transaction_mode="create_savepoint",
        )
        try:
            yield session
        finally:
            await session.close()
            await transaction.rollback()


@pytest.fixture
async def db_client(app: FastAPI, client: AsyncClient, db_session: AsyncSession) -> AsyncClient:
    async def override_get_session() -> AsyncGenerator[AsyncSession]:
        yield db_session
        await db_session.commit()

    app.dependency_overrides[get_session] = override_get_session
    return client
