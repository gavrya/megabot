from sqlalchemy.ext.asyncio import AsyncEngine

from app.modules.health.controllers import health_controller


async def test_check_database_reports_up(db_engine: AsyncEngine) -> None:
    assert await health_controller._check_database() == "up"
