from app.modules.articles.dtos.article_create_dto import ArticleCreateDTO
from app.modules.articles.dtos.article_response_dto import ArticleResponseDTO
from app.modules.articles.dtos.article_update_dto import ArticleUpdateDTO
from app.modules.articles.entities.article_entity import ArticleEntity


class ArticleMapper:
    @staticmethod
    def to_entity(dto: ArticleCreateDTO) -> ArticleEntity:
        return ArticleEntity(title=dto.title, content=dto.content)

    @staticmethod
    def apply_update(entity: ArticleEntity, dto: ArticleUpdateDTO) -> ArticleEntity:
        entity.title = dto.title
        entity.content = dto.content
        return entity

    @staticmethod
    def to_dto(entity: ArticleEntity) -> ArticleResponseDTO:
        return ArticleResponseDTO(
            id=entity.id,
            title=entity.title,
            content=entity.content,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    @classmethod
    def to_dto_list(cls, entities: list[ArticleEntity]) -> list[ArticleResponseDTO]:
        return [cls.to_dto(entity) for entity in entities]
