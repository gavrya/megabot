"""HTTP layer only: the service is replaced by a mock, so no database is involved."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.quotes.controllers import quote_controller
from app.modules.quotes.dtos.quote_create_dto import CreateQuoteDTO
from app.modules.quotes.dtos.quote_response_dto import QuoteResponseDTO
from app.modules.quotes.dtos.quote_update_dto import UpdateQuoteDTO
from app.modules.quotes.repositories.quote_repository import QuoteRepository
from app.modules.quotes.services.quote_service import QuoteService
from app.shared.dtos.page_dto import Page
from app.shared.dtos.page_params_dto import PageParams
from app.shared.exceptions.not_found_error import NotFoundError

URL = "/api/v1/quotes"


def _dto(text: str = "Text") -> QuoteResponseDTO:
    now = datetime.now(UTC)
    return QuoteResponseDTO(id=uuid4(), text=text, author="Author", created_at=now, updated_at=now)


@pytest.fixture
def service(app: FastAPI) -> AsyncMock:
    mock = AsyncMock(spec=QuoteService)
    # The controller resolves its service through its own factory, not dependencies.py.
    app.dependency_overrides[quote_controller.get_quote_service] = lambda: mock
    return mock


def test_get_quote_service_wires_repository_to_session() -> None:
    session = Mock(spec=AsyncSession)

    service = quote_controller.get_quote_service(session)

    assert isinstance(service.repository, QuoteRepository)
    assert service.repository.session is session


async def test_list(client: AsyncClient, service: AsyncMock) -> None:
    item = _dto()
    service.list.return_value = Page(items=[item], total=1, limit=20, offset=0)

    response = await client.get(URL)

    assert response.status_code == 200
    assert response.json()["items"][0]["id"] == str(item.id)
    service.list.assert_awaited_once_with(PageParams())


async def test_list_rejects_invalid_page_params(client: AsyncClient, service: AsyncMock) -> None:
    response = await client.get(URL, params={"limit": 1000})

    assert response.status_code == 422
    service.list.assert_not_awaited()


async def test_get(client: AsyncClient, service: AsyncMock) -> None:
    item = _dto()
    service.get.return_value = item

    response = await client.get(f"{URL}/{item.id}")

    assert response.status_code == 200
    assert response.json()["text"] == item.text
    service.get.assert_awaited_once_with(item.id)


async def test_get_not_found(client: AsyncClient, service: AsyncMock) -> None:
    service.get.side_effect = NotFoundError("Quote x not found")

    response = await client.get(f"{URL}/{uuid4()}")

    assert response.status_code == 404
    assert response.json() == {"code": "not_found", "message": "Quote x not found"}


async def test_create(client: AsyncClient, service: AsyncMock) -> None:
    item = _dto()
    service.create.return_value = item

    response = await client.post(URL, json={"text": "Text", "author": "Author"})

    assert response.status_code == 201
    assert response.json()["id"] == str(item.id)
    service.create.assert_awaited_once_with(CreateQuoteDTO(text="Text", author="Author"))


async def test_create_rejects_invalid_payload(client: AsyncClient, service: AsyncMock) -> None:
    response = await client.post(URL, json={"text": "Text"})

    assert response.status_code == 422
    assert response.json()["details"] == [{"field": "author", "message": "Field required"}]
    service.create.assert_not_awaited()


async def test_update_accepts_partial_payload(client: AsyncClient, service: AsyncMock) -> None:
    item = _dto(text="New")
    service.update.return_value = item

    response = await client.put(f"{URL}/{item.id}", json={"text": "New"})

    assert response.status_code == 200
    service.update.assert_awaited_once_with(item.id, UpdateQuoteDTO.model_validate({"text": "New"}))


async def test_delete(client: AsyncClient, service: AsyncMock) -> None:
    quote_id = uuid4()

    response = await client.delete(f"{URL}/{quote_id}")

    assert response.status_code == 204
    service.delete.assert_awaited_once_with(quote_id)
