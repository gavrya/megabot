"""HTTP layer only: the service is replaced by a mock, so no database is involved."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from app.modules.articles.dependencies import get_article_service
from app.modules.articles.dtos.article_create_dto import ArticleCreateDTO
from app.modules.articles.dtos.article_response_dto import ArticleResponseDTO
from app.modules.articles.dtos.article_update_dto import ArticleUpdateDTO
from app.modules.articles.services.article_service import ArticleService
from app.shared.dtos.page_dto import Page
from app.shared.dtos.page_params_dto import PageParams
from app.shared.exceptions.not_found_error import NotFoundError

URL = "/api/v1/articles"


def _dto(title: str = "Title") -> ArticleResponseDTO:
    now = datetime.now(UTC)
    return ArticleResponseDTO(
        id=uuid4(), title=title, content="Content", created_at=now, updated_at=now
    )


@pytest.fixture
def service(app: FastAPI) -> AsyncMock:
    mock = AsyncMock(spec=ArticleService)
    app.dependency_overrides[get_article_service] = lambda: mock
    return mock


async def test_list(client: AsyncClient, service: AsyncMock) -> None:
    item = _dto()
    service.list.return_value = Page(items=[item], total=1, limit=5, offset=10)

    response = await client.get(URL, params={"limit": 5, "offset": 10})

    assert response.status_code == 200
    service.list.assert_awaited_once_with(PageParams(limit=5, offset=10))
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == str(item.id)


async def test_list_uses_default_page_params(client: AsyncClient, service: AsyncMock) -> None:
    service.list.return_value = Page(items=[], total=0, limit=20, offset=0)

    await client.get(URL)

    service.list.assert_awaited_once_with(PageParams())


@pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 101}, {"offset": -1}])
async def test_list_rejects_invalid_page_params(
    client: AsyncClient, service: AsyncMock, params: dict[str, int]
) -> None:
    response = await client.get(URL, params=params)

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"
    service.list.assert_not_awaited()


async def test_get(client: AsyncClient, service: AsyncMock) -> None:
    item = _dto()
    service.get.return_value = item

    response = await client.get(f"{URL}/{item.id}")

    assert response.status_code == 200
    assert response.json()["title"] == item.title
    service.get.assert_awaited_once_with(item.id)


async def test_get_not_found(client: AsyncClient, service: AsyncMock) -> None:
    service.get.side_effect = NotFoundError("Article x not found")

    response = await client.get(f"{URL}/{uuid4()}")

    assert response.status_code == 404
    assert response.json() == {"code": "not_found", "message": "Article x not found"}


async def test_get_rejects_non_uuid_id(client: AsyncClient, service: AsyncMock) -> None:
    response = await client.get(f"{URL}/123")

    assert response.status_code == 422
    service.get.assert_not_awaited()


async def test_create(client: AsyncClient, service: AsyncMock) -> None:
    item = _dto(title="New")
    service.create.return_value = item

    response = await client.post(URL, json={"title": " New ", "content": "Content"})

    assert response.status_code == 201
    assert response.json()["id"] == str(item.id)
    service.create.assert_awaited_once_with(ArticleCreateDTO(title="New", content="Content"))


async def test_create_rejects_invalid_payload(client: AsyncClient, service: AsyncMock) -> None:
    response = await client.post(URL, json={"title": ""})

    assert response.status_code == 422
    fields = {detail["field"] for detail in response.json()["details"]}
    assert fields == {"title", "content"}
    service.create.assert_not_awaited()


async def test_update(client: AsyncClient, service: AsyncMock) -> None:
    item = _dto(title="Changed")
    service.update.return_value = item

    response = await client.put(f"{URL}/{item.id}", json={"title": "Changed", "content": "C"})

    assert response.status_code == 200
    assert response.json()["title"] == "Changed"
    service.update.assert_awaited_once_with(item.id, ArticleUpdateDTO(title="Changed", content="C"))


async def test_delete(client: AsyncClient, service: AsyncMock) -> None:
    article_id = uuid4()

    response = await client.delete(f"{URL}/{article_id}")

    assert response.status_code == 204
    assert response.content == b""
    service.delete.assert_awaited_once_with(article_id)
