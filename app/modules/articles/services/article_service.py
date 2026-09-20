from app.core.logging import get_logger
from app.modules.articles.dtos.article_dto import (
    ArticleCreateDTO,
    ArticleResponseDTO,
    ArticleUpdateDTO,
)
from app.modules.articles.entities.article_entity import ArticleEntity
from app.modules.articles.mappers.article_mapper import ArticleMapper
from app.modules.articles.repositories.article_repository import ArticleRepository
from app.shared.dtos.base_dto import Page, PageParams
from app.shared.exceptions.base_exceptions import NotFoundError

logger = get_logger(__name__)


class ArticleService:
    def __init__(self, repository: ArticleRepository) -> None:
        self.repository = repository

    async def list(self, params: PageParams) -> Page[ArticleResponseDTO]:
        entities = await self.repository.list(limit=params.limit, offset=params.offset)
        total = await self.repository.count()
        return Page(
            items=ArticleMapper.to_dto_list(entities),
            total=total,
            limit=params.limit,
            offset=params.offset,
        )

    async def get(self, article_id: int) -> ArticleResponseDTO:
        return ArticleMapper.to_dto(await self._get_or_fail(article_id))

    async def create(self, dto: ArticleCreateDTO) -> ArticleResponseDTO:
        entity = await self.repository.add(ArticleMapper.to_entity(dto))
        logger.info("article created", extra={"article_id": entity.id})
        return ArticleMapper.to_dto(entity)

    async def update(self, article_id: int, dto: ArticleUpdateDTO) -> ArticleResponseDTO:
        entity = await self._get_or_fail(article_id)
        entity = await self.repository.update(ArticleMapper.apply_update(entity, dto))
        logger.info("article updated", extra={"article_id": entity.id})
        return ArticleMapper.to_dto(entity)

    async def delete(self, article_id: int) -> None:
        entity = await self._get_or_fail(article_id)
        await self.repository.delete(entity)
        logger.info("article deleted", extra={"article_id": article_id})

    async def _get_or_fail(self, article_id: int) -> ArticleEntity:
        entity = await self.repository.get(article_id)
        if entity is None:
            raise NotFoundError(f"Article {article_id} not found")
        return entity
