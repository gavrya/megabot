"""End to end through the real service and repository against the test database."""

from uuid import uuid4

from httpx import AsyncClient

URL = "/api/v1/quotes"


async def test_crud_flow(db_client: AsyncClient) -> None:
    created = await db_client.post(URL, json={"text": "Be curious", "author": "Someone"})
    assert created.status_code == 201
    quote = created.json()

    fetched = await db_client.get(f"{URL}/{quote['id']}")
    assert fetched.json() == quote

    updated = await db_client.put(f"{URL}/{quote['id']}", json={"author": "Someone else"})
    assert updated.status_code == 200
    assert (updated.json()["text"], updated.json()["author"]) == ("Be curious", "Someone else")

    deleted = await db_client.delete(f"{URL}/{quote['id']}")
    assert deleted.status_code == 204

    missing = await db_client.get(f"{URL}/{quote['id']}")
    assert missing.status_code == 404


async def test_list_returns_created_quotes(db_client: AsyncClient) -> None:
    for text in ("first", "second"):
        await db_client.post(URL, json={"text": text, "author": "A"})

    body = (await db_client.get(URL)).json()

    assert body["total"] == 2
    # Both rows share one transaction, so now() gives them the same created_at.
    assert {item["text"] for item in body["items"]} == {"first", "second"}


async def test_delete_missing_returns_404(db_client: AsyncClient) -> None:
    response = await db_client.delete(f"{URL}/{uuid4()}")

    assert response.status_code == 404
