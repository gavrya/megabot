import pytest
from httpx import AsyncClient

from app.core.config import settings
from app.modules.health.controllers import health_controller


class _UnreachableEngine:
    def connect(self) -> None:
        raise ConnectionRefusedError("connection refused")


@pytest.mark.parametrize(("database", "status"), [("up", "ok"), ("down", "degraded")])
async def test_health_reflects_database_state(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch, database: str, status: str
) -> None:
    async def fake_check() -> str:
        return database

    monkeypatch.setattr(health_controller, "_check_database", fake_check)

    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": status,
        "service": settings.name,
        "environment": settings.env,
        "database": database,
    }


async def test_check_database_reports_down_instead_of_raising(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(health_controller, "engine", _UnreachableEngine())

    assert await health_controller._check_database() == "down"
