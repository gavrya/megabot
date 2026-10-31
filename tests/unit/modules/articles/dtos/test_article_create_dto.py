import pytest
from pydantic import ValidationError

from app.modules.articles.dtos.article_create_dto import ArticleCreateDTO


def test_valid_payload_strips_whitespace() -> None:
    dto = ArticleCreateDTO(title="  Hello  ", content="  Body  ")

    assert dto.title == "Hello"
    assert dto.content == "Body"


@pytest.mark.parametrize(
    ("title", "content"),
    [
        ("", "Body"),
        ("   ", "Body"),
        ("x" * 256, "Body"),
        ("Title", ""),
        ("Title", "   "),
    ],
)
def test_invalid_payload_is_rejected(title: str, content: str) -> None:
    with pytest.raises(ValidationError):
        ArticleCreateDTO(title=title, content=content)


def test_title_at_max_length_is_accepted() -> None:
    assert len(ArticleCreateDTO(title="x" * 255, content="Body").title) == 255


def test_fields_are_required() -> None:
    with pytest.raises(ValidationError) as exc_info:
        ArticleCreateDTO.model_validate({})

    assert {err["loc"][0] for err in exc_info.value.errors()} == {"title", "content"}
