from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.articles.entities.article_entity import ArticleEntity
from app.modules.articles.repositories.article_repository import ArticleRepository


async def test_round_trip(db_session: AsyncSession) -> None:
    repository = ArticleRepository(db_session)

    created = await repository.add(ArticleEntity(title="Title", content="Content"))
    fetched = await repository.get(created.id)

    assert fetched is not None
    assert (fetched.title, fetched.content) == ("Title", "Content")
    assert await repository.count() == 1
