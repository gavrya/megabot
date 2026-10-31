from typing import cast

from sqlalchemy import Table

from app.modules.articles.entities.article_entity import ArticleEntity
from app.shared.entities.base_entity import NAMING_CONVENTION, Base

table = cast(Table, ArticleEntity.__table__)


def test_metadata_uses_naming_convention() -> None:
    assert Base.metadata.naming_convention == NAMING_CONVENTION


def test_primary_keys_follow_convention() -> None:
    assert table.primary_key.name == "pk_articles"


def test_indexes_follow_convention() -> None:
    assert {index.name for index in table.indexes} == {"ix_articles_title"}
