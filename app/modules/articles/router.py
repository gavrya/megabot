from fastapi import APIRouter

from app.modules.articles.controllers import article_controller

# The prefix is applied here, so controllers stay path-agnostic.
router = APIRouter()
router.include_router(article_controller.router, prefix="/articles", tags=["articles"])
