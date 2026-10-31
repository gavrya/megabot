from fastapi import FastAPI

from app.modules.quotes.router import router


def test_routes_are_prefixed_and_tagged() -> None:
    app = FastAPI()
    app.include_router(router)
    paths = app.openapi()["paths"]

    assert {path: set(operations) for path, operations in paths.items()} == {
        "/quotes": {"get", "post"},
        "/quotes/{quote_id}": {"get", "put", "delete"},
    }
    assert all(
        operation["tags"] == ["quotes"]
        for operations in paths.values()
        for operation in operations.values()
    )
