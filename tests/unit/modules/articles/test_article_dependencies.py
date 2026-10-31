from unittest.mock import Mock

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.articles.dependencies import get_article_service
from app.modules.articles.repositories.article_repository import ArticleRepository
from app.modules.articles.services.article_service import ArticleService


def test_wires_repository_to_session() -> None:
    session = Mock(spec=AsyncSession)

    service = get_article_service(session)

    assert isinstance(service, ArticleService)
    assert isinstance(service.repository, ArticleRepository)
    assert service.repository.session is session
