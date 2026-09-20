from app.modules.articles.entities.article_entity import ArticleEntity
from app.shared.repositories.base_repository import BaseRepository


class ArticleRepository(BaseRepository[ArticleEntity]):
    model = ArticleEntity
