from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.modules.quotes.dtos.quote_create_dto import CreateQuoteDTO
from app.modules.quotes.dtos.quote_update_dto import UpdateQuoteDTO
from app.modules.quotes.entities.quote_entity import QuoteEntity
from app.modules.quotes.repositories.quote_repository import QuoteRepository
from app.modules.quotes.services.quote_service import QuoteService
from app.shared.dtos.page_params_dto import PageParams
from app.shared.exceptions.not_found_error import NotFoundError


def _entity(text: str = "Text", author: str = "Author") -> QuoteEntity:
    now = datetime.now(UTC)
    return QuoteEntity(id=uuid4(), text=text, author=author, created_at=now, updated_at=now)


@pytest.fixture
def repository() -> AsyncMock:
    return AsyncMock(spec=QuoteRepository)


@pytest.fixture
def service(repository: AsyncMock) -> QuoteService:
    return QuoteService(repository)


async def test_list_returns_page(service: QuoteService, repository: AsyncMock) -> None:
    entities = [_entity(text="a"), _entity(text="b")]
    repository.list.return_value = entities
    repository.count.return_value = 2

    page = await service.list(PageParams(limit=10, offset=0))

    repository.list.assert_awaited_once_with(limit=10, offset=0)
    assert [item.text for item in page.items] == ["a", "b"]
    assert (page.total, page.limit, page.offset) == (2, 10, 0)


async def test_get_returns_dto(service: QuoteService, repository: AsyncMock) -> None:
    entity = _entity()
    repository.get.return_value = entity

    dto = await service.get(entity.id)

    assert dto.id == entity.id


async def test_get_missing_raises_not_found(service: QuoteService, repository: AsyncMock) -> None:
    repository.get.return_value = None
    quote_id = uuid4()

    with pytest.raises(NotFoundError, match=str(quote_id)):
        await service.get(quote_id)


async def test_create_adds_mapped_entity(service: QuoteService, repository: AsyncMock) -> None:
    stored = _entity()
    repository.add.return_value = stored

    dto = await service.create(CreateQuoteDTO(text="Text", author="Author"))

    added = repository.add.await_args.args[0]
    assert (added.text, added.author) == ("Text", "Author")
    assert dto.id == stored.id


async def test_update_applies_partial_changes(service: QuoteService, repository: AsyncMock) -> None:
    entity = _entity(text="Old", author="Author")
    repository.get.return_value = entity
    repository.update.side_effect = lambda e: e

    dto = await service.update(entity.id, UpdateQuoteDTO.model_validate({"text": "New"}))

    repository.update.assert_awaited_once_with(entity)
    assert (dto.text, dto.author) == ("New", "Author")


async def test_update_missing_raises_not_found(
    service: QuoteService, repository: AsyncMock
) -> None:
    repository.get.return_value = None

    with pytest.raises(NotFoundError):
        await service.update(uuid4(), UpdateQuoteDTO.model_validate({"text": "New"}))
    repository.update.assert_not_awaited()


async def test_delete_removes_entity(service: QuoteService, repository: AsyncMock) -> None:
    entity = _entity()
    repository.get.return_value = entity

    await service.delete(entity.id)

    repository.delete.assert_awaited_once_with(entity)


async def test_delete_missing_raises_not_found(
    service: QuoteService, repository: AsyncMock
) -> None:
    repository.get.return_value = None

    with pytest.raises(NotFoundError):
        await service.delete(uuid4())
    repository.delete.assert_not_awaited()
