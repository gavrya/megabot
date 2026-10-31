from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy import String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.articles.entities.article_entity import ArticleEntity
from app.shared.entities.base_entity import Base
from app.shared.entities.uuid_primary_key_mixin import UuidPrimaryKeyMixin
from app.shared.repositories.base_repository import BaseRepository


class _UntimedEntity(UuidPrimaryKeyMixin, Base):
    """Test-only table without timestamps, to exercise the order-by-id fallback."""

    __tablename__ = "test_untimed"

    name: Mapped[str] = mapped_column(String(50))


class _ArticleRepository(BaseRepository[ArticleEntity]):
    model = ArticleEntity


class _UntimedRepository(BaseRepository[_UntimedEntity]):
    model = _UntimedEntity


@pytest.fixture
def repository(db_session: AsyncSession) -> _ArticleRepository:
    return _ArticleRepository(db_session)


async def _add_articles(repository: _ArticleRepository, count: int) -> list[ArticleEntity]:
    base = datetime(2026, 1, 1, tzinfo=UTC)
    return [
        await repository.add(
            ArticleEntity(
                title=f"Article {index}",
                content="Body",
                created_at=base + timedelta(minutes=index),
            )
        )
        for index in range(count)
    ]


async def test_add_assigns_id_and_server_defaults(repository: _ArticleRepository) -> None:
    entity = await repository.add(ArticleEntity(title="T", content="C"))

    assert isinstance(entity.id, UUID)
    assert entity.created_at is not None
    assert entity.updated_at is not None


async def test_get_returns_entity_or_none(repository: _ArticleRepository) -> None:
    [entity] = await _add_articles(repository, 1)

    assert await repository.get(entity.id) is entity
    assert await repository.get(uuid4()) is None


async def test_list_is_newest_first(repository: _ArticleRepository) -> None:
    entities = await _add_articles(repository, 3)

    result = await repository.list(limit=10, offset=0)

    assert [entity.id for entity in result] == [entity.id for entity in reversed(entities)]


async def test_list_applies_limit_and_offset(repository: _ArticleRepository) -> None:
    entities = await _add_articles(repository, 5)

    result = await repository.list(limit=2, offset=1)

    assert [entity.title for entity in result] == [entities[3].title, entities[2].title]
    assert await repository.list(limit=10, offset=5) == []


async def test_list_orders_by_id_without_created_at(db_session: AsyncSession) -> None:
    repository = _UntimedRepository(db_session)
    entities = [await repository.add(_UntimedEntity(name=str(index))) for index in range(3)]

    result = await repository.list(limit=10, offset=0)

    assert [entity.id for entity in result] == sorted(
        (entity.id for entity in entities), reverse=True
    )


async def test_count(repository: _ArticleRepository) -> None:
    assert await repository.count() == 0

    await _add_articles(repository, 3)

    assert await repository.count() == 3


async def test_update_flushes_and_refreshes(repository: _ArticleRepository) -> None:
    [entity] = await _add_articles(repository, 1)
    entity.title = "Changed"

    updated = await repository.update(entity)

    assert updated is entity
    fetched = await repository.get(entity.id)
    assert fetched is not None
    assert fetched.title == "Changed"


async def test_delete_removes_row(repository: _ArticleRepository) -> None:
    [entity] = await _add_articles(repository, 1)

    await repository.delete(entity)

    assert await repository.get(entity.id) is None
    assert await repository.count() == 0
