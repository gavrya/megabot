from fastapi import APIRouter

from app.modules.health.controllers import health_controller

router = APIRouter()
router.include_router(health_controller.router, tags=["health"])
