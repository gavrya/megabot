from collections.abc import AsyncGenerator

import pytest
from fastapi import FastAPI, HTTPException
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel

from app.shared.exceptions.conflict_error import ConflictError
from app.shared.exceptions.exception_handlers import register_exception_handlers
from app.shared.exceptions.not_found_error import NotFoundError


class _Payload(BaseModel):
    name: str
    count: int


def _build_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/not-found")
    async def not_found() -> None:
        raise NotFoundError("Thing 1 not found")

    @app.get("/conflict")
    async def conflict() -> None:
        raise ConflictError()

    @app.get("/http-error")
    async def http_error() -> None:
        raise HTTPException(status_code=403, detail="Forbidden here")

    @app.get("/crash")
    async def crash() -> None:
        raise RuntimeError("secret internals")

    @app.post("/validate")
    async def validate(payload: _Payload) -> _Payload:
        return payload

    return app


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient]:
    # Unhandled errors are re-raised by Starlette after the handler responds; keep the response.
    transport = ASGITransport(app=_build_app(), raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client


async def test_app_error_uses_its_status_and_code(client: AsyncClient) -> None:
    response = await client.get("/not-found")

    assert response.status_code == 404
    assert response.json() == {"code": "not_found", "message": "Thing 1 not found"}


async def test_app_error_subclass_default_message(client: AsyncClient) -> None:
    response = await client.get("/conflict")

    assert response.status_code == 409
    assert response.json() == {
        "code": "conflict",
        "message": "Requested change conflicts with the current state.",
    }


async def test_validation_error_lists_fields_without_location_prefix(client: AsyncClient) -> None:
    response = await client.post("/validate", json={"count": "many"})

    assert response.status_code == 422
    body = response.json()
    assert (body["code"], body["message"]) == ("validation_error", "Request validation failed")
    assert {detail["field"] for detail in body["details"]} == {"name", "count"}
    assert all(detail["message"] for detail in body["details"])


async def test_http_exception_keeps_status(client: AsyncClient) -> None:
    response = await client.get("/http-error")

    assert response.status_code == 403
    assert response.json() == {"code": "http_error", "message": "Forbidden here"}


async def test_unknown_route_is_http_error(client: AsyncClient) -> None:
    response = await client.get("/missing")

    assert response.status_code == 404
    assert response.json() == {"code": "http_error", "message": "Not Found"}


async def test_unexpected_error_hides_details(
    client: AsyncClient, caplog: pytest.LogCaptureFixture
) -> None:
    response = await client.get("/crash")

    assert response.status_code == 500
    assert response.json() == {"code": "internal_error", "message": "Internal server error"}
    assert "secret internals" not in response.text
    assert "unhandled error" in caplog.text
