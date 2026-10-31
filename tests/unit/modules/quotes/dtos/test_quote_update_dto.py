import pytest
from pydantic import ValidationError

from app.modules.quotes.dtos.quote_update_dto import UpdateQuoteDTO


def test_every_field_is_optional() -> None:
    dto = UpdateQuoteDTO.model_validate({})

    assert (dto.text, dto.author) == (None, None)


def test_partial_payload_strips_whitespace() -> None:
    dto = UpdateQuoteDTO.model_validate({"author": "  Someone  "})

    assert dto.author == "Someone"
    assert dto.text is None


@pytest.mark.parametrize("payload", [{"text": ""}, {"author": ""}, {"author": "x" * 256}])
def test_invalid_values_are_rejected(payload: dict[str, str]) -> None:
    with pytest.raises(ValidationError):
        UpdateQuoteDTO.model_validate(payload)
