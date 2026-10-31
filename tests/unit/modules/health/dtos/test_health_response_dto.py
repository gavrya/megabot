import pytest
from pydantic import ValidationError

from app.modules.health.dtos.health_response_dto import HealthResponseDTO


def test_holds_every_field() -> None:
    dto = HealthResponseDTO(status="ok", service="megabot", environment="local", database="up")

    assert dto.model_dump() == {
        "status": "ok",
        "service": "megabot",
        "environment": "local",
        "database": "up",
    }


def test_fields_are_required() -> None:
    with pytest.raises(ValidationError):
        HealthResponseDTO.model_validate({"status": "ok"})
