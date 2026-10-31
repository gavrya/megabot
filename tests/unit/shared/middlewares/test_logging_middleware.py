import logging
from collections.abc import AsyncGenerator
from uuid import UUID

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.core.logging import request_id_var
from app.shared.middlewares.logging_middleware import REQUEST_ID_HEADER, RequestContextMiddleware

LOGGER = "app.shared.middlewares.logging_middleware"


def _build_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(RequestContextMiddleware)

    @app.get("/echo")
    async def echo() -> dict[str, str | None]:
        return {"request_id": request_id_var.get()}

    @app.get("/crash")
    async def crash() -> None:
        raise RuntimeError("boom")

    return app


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient]:
    transport = ASGITransport(app=_build_app(), raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client


async def test_generates_request_id(client: AsyncClient) -> None:
    response = await client.get("/echo")

    request_id = response.headers[REQUEST_ID_HEADER]
    assert UUID(request_id)
    assert response.json() == {"request_id": request_id}


async def test_propagates_incoming_request_id(client: AsyncClient) -> None:
    response = await client.get("/echo", headers={REQUEST_ID_HEADER: "abc-123"})

    assert response.headers[REQUEST_ID_HEADER] == "abc-123"
    assert response.json() == {"request_id": "abc-123"}


async def test_resets_request_id_after_request(client: AsyncClient) -> None:
    await client.get("/echo", headers={REQUEST_ID_HEADER: "abc-123"})

    assert request_id_var.get() is None


async def test_logs_access_line_with_timing(
    client: AsyncClient, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.INFO, logger=LOGGER):
        await client.get("/echo")

    [record] = [r for r in caplog.records if r.name == LOGGER]
    assert record.getMessage().startswith("GET /echo 200")
    assert record.__dict__["method"] == "GET"
    assert record.__dict__["path"] == "/echo"
    assert record.__dict__["status_code"] == 200
    assert record.__dict__["duration_ms"] >= 0


async def test_logs_and_reraises_failures(
    client: AsyncClient, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.INFO, logger=LOGGER):
        response = await client.get("/crash")

    assert response.status_code == 500
    [record] = [r for r in caplog.records if r.name == LOGGER]
    assert record.getMessage() == "request failed"
    assert record.levelno == logging.ERROR
    assert record.exc_info is not None
    assert request_id_var.get() is None
