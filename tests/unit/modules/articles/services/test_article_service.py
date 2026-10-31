from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.modules.articles.dtos.article_create_dto import ArticleCreateDTO
from app.modules.articles.dtos.article_update_dto import ArticleUpdateDTO
from app.modules.articles.entities.article_entity import ArticleEntity
from app.modules.articles.repositories.article_repository import ArticleRepository
from app.modules.articles.services.article_service import ArticleService
from app.shared.dtos.page_params_dto import PageParams
from app.shared.exceptions.not_found_error import NotFoundError


def _entity(title: str = "Title", content: str = "Content") -> ArticleEntity:
    now = datetime.now(UTC)
    return ArticleEntity(id=uuid4(), title=title, content=content, created_at=now, updated_at=now)


@pytest.fixture
def repository() -> AsyncMock:
    return AsyncMock(spec=ArticleRepository)


@pytest.fixture
def service(repository: AsyncMock) -> ArticleService:
    return ArticleService(repository)


async def test_list_returns_page(service: ArticleService, repository: AsyncMock) -> None:
    entities = [_entity(title="a"), _entity(title="b")]
    repository.list.return_value = entities
    repository.count.return_value = 7

    page = await service.list(PageParams(limit=2, offset=4))

    repository.list.assert_awaited_once_with(limit=2, offset=4)
    assert [item.id for item in page.items] == [entity.id for entity in entities]
    assert (page.total, page.limit, page.offset) == (7, 2, 4)


async def test_get_returns_dto(service: ArticleService, repository: AsyncMock) -> None:
    entity = _entity()
    repository.get.return_value = entity

    dto = await service.get(entity.id)

    repository.get.assert_awaited_once_with(entity.id)
    assert dto.id == entity.id
    assert dto.title == entity.title


async def test_get_missing_raises_not_found(service: ArticleService, repository: AsyncMock) -> None:
    repository.get.return_value = None
    article_id = uuid4()

    with pytest.raises(NotFoundError, match=str(article_id)):
        await service.get(article_id)


async def test_create_adds_mapped_entity(service: ArticleService, repository: AsyncMock) -> None:
    stored = _entity(title="New", content="Body")
    repository.add.return_value = stored

    dto = await service.create(ArticleCreateDTO(title="New", content="Body"))

    added = repository.add.await_args.args[0]
    assert isinstance(added, ArticleEntity)
    assert (added.title, added.content) == ("New", "Body")
    assert dto.id == stored.id


async def test_update_applies_changes(service: ArticleService, repository: AsyncMock) -> None:
    entity = _entity()
    repository.get.return_value = entity
    repository.update.side_effect = lambda e: e

    dto = await service.update(entity.id, ArticleUpdateDTO(title="Changed", content="Text"))

    repository.update.assert_awaited_once_with(entity)
    assert (dto.title, dto.content) == ("Changed", "Text")


async def test_update_missing_raises_not_found(
    service: ArticleService, repository: AsyncMock
) -> None:
    repository.get.return_value = None

    with pytest.raises(NotFoundError):
        await service.update(uuid4(), ArticleUpdateDTO(title="T", content="C"))
    repository.update.assert_not_awaited()


async def test_delete_removes_entity(service: ArticleService, repository: AsyncMock) -> None:
    entity = _entity()
    repository.get.return_value = entity

    await service.delete(entity.id)

    repository.delete.assert_awaited_once_with(entity)


async def test_delete_missing_raises_not_found(
    service: ArticleService, repository: AsyncMock
) -> None:
    repository.get.return_value = None

    with pytest.raises(NotFoundError):
        await service.delete(uuid4())
    repository.delete.assert_not_awaited()
