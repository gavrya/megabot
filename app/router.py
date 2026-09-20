from fastapi import APIRouter

from app.modules.articles.router import router as articles_router
from app.modules.health.router import router as health_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(articles_router, prefix="/api/v1")
