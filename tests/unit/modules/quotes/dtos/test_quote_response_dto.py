from datetime import UTC, datetime
from uuid import uuid4

from app.modules.quotes.dtos.quote_response_dto import QuoteResponseDTO
from app.modules.quotes.entities.quote_entity import QuoteEntity


def test_builds_from_entity_attributes() -> None:
    now = datetime.now(UTC)
    entity = QuoteEntity(id=uuid4(), text="T", author="A", created_at=now, updated_at=now)

    dto = QuoteResponseDTO.model_validate(entity)

    assert dto.model_dump() == {
        "id": entity.id,
        "text": "T",
        "author": "A",
        "created_at": now,
        "updated_at": now,
    }


def test_serializes_to_json_types() -> None:
    quote_id = uuid4()
    now = datetime(2026, 1, 2, tzinfo=UTC)

    dto = QuoteResponseDTO(id=quote_id, text="T", author="A", created_at=now, updated_at=now)

    assert dto.model_dump(mode="json")["id"] == str(quote_id)
    assert dto.model_dump(mode="json")["created_at"] == "2026-01-02T00:00:00Z"
