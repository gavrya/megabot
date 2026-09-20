from typing import Annotated

from fastapi import Depends

from app.modules.articles.repositories.article_repository import ArticleRepository
from app.modules.articles.services.article_service import ArticleService
from app.shared.dependencies import SessionDep


def get_article_service(session: SessionDep) -> ArticleService:
    return ArticleService(ArticleRepository(session))


ArticleServiceDep = Annotated[ArticleService, Depends(get_article_service)]
