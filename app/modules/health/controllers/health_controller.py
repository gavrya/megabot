from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import settings
from app.core.database import engine
from app.core.logging import get_logger
from app.modules.health.dtos.health_response_dto import HealthResponseDTO

router = APIRouter()
logger = get_logger(__name__)


async def _check_database() -> str:
    # Own connection, not the request session: a dead DB must not fail the response.
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception as exc:
        logger.warning("database health check failed: %s", exc)
        return "down"
    return "up"


@router.get("/health", response_model=HealthResponseDTO)
async def health() -> HealthResponseDTO:
    database = await _check_database()
    return HealthResponseDTO(
        status="ok" if database == "up" else "degraded",
        service=settings.app_name,
        environment=settings.app_env,
        database=database,
    )
