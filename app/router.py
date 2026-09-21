from fastapi import APIRouter

from app.modules.articles.router import router as articles_router
from app.modules.health.router import router as health_router
from app.modules.quotes.router import router as quotes_router

api_router = APIRouter()
api_router.include_router(health_router)

# Business modules are versioned under /api/v1
api_router.include_router(articles_router, prefix="/api/v1")
api_router.include_router(quotes_router, prefix="/api/v1")
