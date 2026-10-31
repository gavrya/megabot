from datetime import UTC, datetime
from uuid import uuid4

from app.modules.articles.dtos.article_create_dto import ArticleCreateDTO
from app.modules.articles.dtos.article_update_dto import ArticleUpdateDTO
from app.modules.articles.entities.article_entity import ArticleEntity
from app.modules.articles.mappers.article_mapper import ArticleMapper


def _entity(title: str = "Title", content: str = "Content") -> ArticleEntity:
    now = datetime.now(UTC)
    return ArticleEntity(id=uuid4(), title=title, content=content, created_at=now, updated_at=now)


def test_to_entity_copies_fields() -> None:
    entity = ArticleMapper.to_entity(ArticleCreateDTO(title="Hello", content="World"))

    assert isinstance(entity, ArticleEntity)
    assert entity.title == "Hello"
    assert entity.content == "World"


def test_apply_update_overwrites_fields_in_place() -> None:
    entity = _entity()

    result = ArticleMapper.apply_update(entity, ArticleUpdateDTO(title="New", content="Body"))

    assert result is entity
    assert (entity.title, entity.content) == ("New", "Body")


def test_to_dto_copies_every_field() -> None:
    entity = _entity()

    dto = ArticleMapper.to_dto(entity)

    assert dto.model_dump() == {
        "id": entity.id,
        "title": entity.title,
        "content": entity.content,
        "created_at": entity.created_at,
        "updated_at": entity.updated_at,
    }


def test_to_dto_list_preserves_order() -> None:
    entities = [_entity(title="a"), _entity(title="b")]

    assert [dto.title for dto in ArticleMapper.to_dto_list(entities)] == ["a", "b"]
    assert ArticleMapper.to_dto_list([]) == []
