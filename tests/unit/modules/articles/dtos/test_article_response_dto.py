from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.modules.articles.dtos.article_response_dto import ArticleResponseDTO


def test_serializes_to_json_types() -> None:
    article_id = uuid4()
    now = datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)

    dto = ArticleResponseDTO(id=article_id, title="T", content="C", created_at=now, updated_at=now)

    assert dto.model_dump(mode="json") == {
        "id": str(article_id),
        "title": "T",
        "content": "C",
        "created_at": "2026-01-02T03:04:05Z",
        "updated_at": "2026-01-02T03:04:05Z",
    }


def test_rejects_invalid_id() -> None:
    now = datetime.now(UTC)
    with pytest.raises(ValidationError):
        ArticleResponseDTO.model_validate(
            {"id": "not-a-uuid", "title": "T", "content": "C", "created_at": now, "updated_at": now}
        )
