"""Fixtures shared by unit and integration tests.

Tests are split by directory: `tests/unit/` needs nothing running, `tests/integration/` needs
PostgreSQL (its fixtures live in `tests/integration/conftest.py`). Each test is also marked
`unit` or `integration` after its directory, so `-m` selects them across any path.
"""

from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.main import app as fastapi_app

TESTS_DIR = Path(__file__).parent


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        kind = item.path.relative_to(TESTS_DIR).parts[0]
        if kind in ("unit", "integration"):
            item.add_marker(getattr(pytest.mark, kind))


@pytest.fixture
def app() -> FastAPI:
    return fastapi_app


@pytest.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client
    app.dependency_overrides.clear()
