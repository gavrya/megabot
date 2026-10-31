from typing import cast
from uuid import UUID

from sqlalchemy import Table, Uuid

from app.modules.articles.entities.article_entity import ArticleEntity

table = cast(Table, ArticleEntity.__table__)


def test_id_is_uuid_primary_key_sorted_first() -> None:
    column = table.c.id

    assert isinstance(column.type, Uuid)
    assert column.primary_key is True
    assert next(iter(table.columns.keys())) == "id"


def test_app_generates_a_fresh_uuid() -> None:
    default = table.c.id.default
    assert default is not None

    first, second = default.arg(None), default.arg(None)  # pyright: ignore[reportAttributeAccessIssue]

    assert isinstance(first, UUID)
    assert first != second


def test_database_generates_uuid_for_rows_inserted_outside_the_orm() -> None:
    server_default = table.c.id.server_default

    assert server_default is not None
    assert "gen_random_uuid" in str(server_default.arg)  # pyright: ignore[reportAttributeAccessIssue]
