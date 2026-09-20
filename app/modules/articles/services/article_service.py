from uuid import UUID

from app.core.logging import get_logger
from app.modules.articles.dtos.article_create_dto import ArticleCreateDTO
from app.modules.articles.dtos.article_response_dto import ArticleResponseDTO
from app.modules.articles.dtos.article_update_dto import ArticleUpdateDTO
from app.modules.articles.entities.article_entity import ArticleEntity
from app.modules.articles.mappers.article_mapper import ArticleMapper
from app.modules.articles.repositories.article_repository import ArticleRepository
from app.shared.dtos.page_dto import Page
from app.shared.dtos.page_params_dto import PageParams
from app.shared.exceptions.not_found_error import NotFoundError

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

    async def get(self, article_id: UUID) -> ArticleResponseDTO:
        return ArticleMapper.to_dto(await self._get_or_fail(article_id))

    async def create(self, dto: ArticleCreateDTO) -> ArticleResponseDTO:
        entity = await self.repository.add(ArticleMapper.to_entity(dto))
        logger.info("article created", extra={"article_id": entity.id})
        return ArticleMapper.to_dto(entity)

    async def update(self, article_id: UUID, dto: ArticleUpdateDTO) -> ArticleResponseDTO:
        entity = await self._get_or_fail(article_id)
        entity = await self.repository.update(ArticleMapper.apply_update(entity, dto))
        logger.info("article updated", extra={"article_id": entity.id})
        return ArticleMapper.to_dto(entity)

    async def delete(self, article_id: UUID) -> None:
        entity = await self._get_or_fail(article_id)
        await self.repository.delete(entity)
        logger.info("article deleted", extra={"article_id": article_id})

    async def _get_or_fail(self, article_id: UUID) -> ArticleEntity:
        entity = await self.repository.get(article_id)
        if entity is None:
            raise NotFoundError(f"Article {article_id} not found")
        return entity
