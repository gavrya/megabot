from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.modules.quotes.dtos.quote_create_dto import CreateQuoteDTO
from app.modules.quotes.dtos.quote_update_dto import UpdateQuoteDTO
from app.modules.quotes.entities.quote_entity import QuoteEntity
from app.modules.quotes.mappers.quote_mapper import QuoteMapper


def _entity(text: str = "Text", author: str = "Author") -> QuoteEntity:
    now = datetime.now(UTC)
    return QuoteEntity(id=uuid4(), text=text, author=author, created_at=now, updated_at=now)


def test_to_entity_copies_fields() -> None:
    entity = QuoteMapper.to_entity(CreateQuoteDTO(text="Text", author="Author"))

    assert isinstance(entity, QuoteEntity)
    assert (entity.text, entity.author) == ("Text", "Author")


def test_to_dto_copies_every_field() -> None:
    entity = _entity()

    dto = QuoteMapper.to_dto(entity)

    assert (dto.id, dto.text, dto.author) == (entity.id, entity.text, entity.author)
    assert (dto.created_at, dto.updated_at) == (entity.created_at, entity.updated_at)


def test_to_dto_list_preserves_order() -> None:
    entities = [_entity(text="a"), _entity(text="b")]

    assert [dto.text for dto in QuoteMapper.to_dto_list(entities)] == ["a", "b"]


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        ({}, ("Old text", "Old author")),
        ({"text": "New text"}, ("New text", "Old author")),
        ({"author": "New author"}, ("Old text", "New author")),
        ({"text": "New text", "author": "New author"}, ("New text", "New author")),
    ],
)
def test_apply_update_changes_only_provided_fields(
    payload: dict[str, str], expected: tuple[str, str]
) -> None:
    entity = _entity(text="Old text", author="Old author")

    result = QuoteMapper.apply_update(entity, UpdateQuoteDTO.model_validate(payload))

    assert result is entity
    assert (entity.text, entity.author) == expected
