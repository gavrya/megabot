from app.modules.articles.entities.article_entity import ArticleEntity
from app.modules.articles.repositories.article_repository import ArticleRepository
from app.shared.repositories.base_repository import BaseRepository


def test_is_bound_to_article_entity() -> None:
    assert issubclass(ArticleRepository, BaseRepository)
    assert ArticleRepository.model is ArticleEntity
