from typing import cast

from sqlalchemy import String, Table, Text

from app.modules.articles.entities.article_entity import ArticleEntity
from app.shared.entities.base_entity import Base

table = cast(Table, ArticleEntity.__table__)


def test_is_registered_on_shared_metadata() -> None:
    assert Base.metadata.tables["articles"] is table


def test_columns_in_mixin_order() -> None:
    assert list(table.columns.keys()) == ["id", "title", "content", "created_at", "updated_at"]


def test_title_column() -> None:
    title = table.c.title
    assert isinstance(title.type, String)
    assert title.type.length == 255
    assert title.nullable is False
    assert title.index is True


def test_content_column() -> None:
    content = table.c.content
    assert isinstance(content.type, Text)
    assert content.nullable is False


def test_primary_key_is_id() -> None:
    assert [column.name for column in table.primary_key] == ["id"]
