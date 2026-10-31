"""End to end through the real service and repository against the test database."""

from uuid import uuid4

from httpx import AsyncClient

URL = "/api/v1/articles"


async def test_crud_flow(db_client: AsyncClient) -> None:
    created = await db_client.post(URL, json={"title": "First", "content": "Body"})
    assert created.status_code == 201
    article = created.json()
    assert article["title"] == "First"
    assert article["created_at"] is not None

    fetched = await db_client.get(f"{URL}/{article['id']}")
    assert fetched.status_code == 200
    assert fetched.json() == article

    updated = await db_client.put(
        f"{URL}/{article['id']}", json={"title": "Second", "content": "New body"}
    )
    assert updated.status_code == 200
    assert (updated.json()["title"], updated.json()["content"]) == ("Second", "New body")

    deleted = await db_client.delete(f"{URL}/{article['id']}")
    assert deleted.status_code == 204

    missing = await db_client.get(f"{URL}/{article['id']}")
    assert missing.status_code == 404
    assert missing.json()["code"] == "not_found"


async def test_list_paginates(db_client: AsyncClient) -> None:
    for index in range(3):
        await db_client.post(URL, json={"title": f"Article {index}", "content": "Body"})

    response = await db_client.get(URL, params={"limit": 2, "offset": 1})

    body = response.json()
    assert response.status_code == 200
    assert body["total"] == 3
    assert (body["limit"], body["offset"]) == (2, 1)
    assert len(body["items"]) == 2


async def test_update_missing_returns_404(db_client: AsyncClient) -> None:
    response = await db_client.put(f"{URL}/{uuid4()}", json={"title": "T", "content": "C"})

    assert response.status_code == 404


async def test_delete_missing_returns_404(db_client: AsyncClient) -> None:
    response = await db_client.delete(f"{URL}/{uuid4()}")

    assert response.status_code == 404
