import pytest
from pydantic import ValidationError

from app.modules.articles.dtos.article_update_dto import ArticleUpdateDTO


def test_valid_payload_strips_whitespace() -> None:
    dto = ArticleUpdateDTO(title="  New  ", content="  Text  ")

    assert dto.title == "New"
    assert dto.content == "Text"


def test_full_replace_requires_every_field() -> None:
    with pytest.raises(ValidationError) as exc_info:
        ArticleUpdateDTO.model_validate({"title": "Only title"})

    assert [err["loc"][0] for err in exc_info.value.errors()] == ["content"]


@pytest.mark.parametrize(
    ("title", "content"),
    [("", "Body"), ("x" * 256, "Body"), ("Title", "")],
)
def test_invalid_payload_is_rejected(title: str, content: str) -> None:
    with pytest.raises(ValidationError):
        ArticleUpdateDTO(title=title, content=content)
