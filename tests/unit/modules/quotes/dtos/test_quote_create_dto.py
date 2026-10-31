import pytest
from pydantic import ValidationError

from app.modules.quotes.dtos.quote_create_dto import CreateQuoteDTO


def test_valid_payload_strips_whitespace() -> None:
    dto = CreateQuoteDTO(text="  Stay hungry  ", author="  Jobs ")

    assert dto.text == "Stay hungry"
    assert dto.author == "Jobs"


@pytest.mark.parametrize(
    ("text", "author"),
    [("", "Author"), ("   ", "Author"), ("Text", ""), ("Text", "x" * 256)],
)
def test_invalid_payload_is_rejected(text: str, author: str) -> None:
    with pytest.raises(ValidationError):
        CreateQuoteDTO(text=text, author=author)


def test_fields_are_required() -> None:
    with pytest.raises(ValidationError) as exc_info:
        CreateQuoteDTO.model_validate({})

    assert {err["loc"][0] for err in exc_info.value.errors()} == {"text", "author"}
