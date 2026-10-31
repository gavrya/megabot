from typing import cast

from sqlalchemy import DateTime, Table

from app.modules.articles.entities.article_entity import ArticleEntity
from app.shared.entities.timestamp_mixin import TimestampMixin

table = cast(Table, ArticleEntity.__table__)


def test_columns_are_tz_aware_and_required() -> None:
    for name in ("created_at", "updated_at"):
        column = table.c[name]
        assert isinstance(column.type, DateTime)
        assert column.type.timezone is True
        assert column.nullable is False
        assert column.server_default is not None


def test_only_updated_at_changes_on_update() -> None:
    assert table.c.created_at.onupdate is None
    assert table.c.updated_at.onupdate is not None


def test_columns_sort_last() -> None:
    assert issubclass(ArticleEntity, TimestampMixin)
    assert list(table.columns.keys())[-2:] == ["created_at", "updated_at"]
