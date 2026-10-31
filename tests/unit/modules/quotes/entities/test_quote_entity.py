from typing import cast

from sqlalchemy import String, Table, Text

from app.modules.quotes.entities.quote_entity import QuoteEntity
from app.shared.entities.base_entity import Base

table = cast(Table, QuoteEntity.__table__)


def test_is_registered_on_shared_metadata() -> None:
    assert Base.metadata.tables["quotes"] is table


def test_columns_in_mixin_order() -> None:
    assert list(table.columns.keys()) == ["id", "text", "author", "created_at", "updated_at"]


def test_text_column() -> None:
    assert isinstance(table.c.text.type, Text)
    assert table.c.text.nullable is False


def test_author_column() -> None:
    author = table.c.author
    assert isinstance(author.type, String)
    assert author.type.length == 255
    assert author.nullable is False
    assert author.index is True
