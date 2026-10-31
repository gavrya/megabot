from fastapi import FastAPI

from app.modules.health.router import router


def test_health_route_is_unprefixed_and_tagged() -> None:
    app = FastAPI()
    app.include_router(router)
    paths = app.openapi()["paths"]

    assert list(paths) == ["/health"]
    assert list(paths["/health"]) == ["get"]
    assert paths["/health"]["get"]["tags"] == ["health"]
