from uuid import UUID

from app.core.logging import get_logger
from app.modules.quotes.dtos.quote_create_dto import CreateQuoteDTO
from app.modules.quotes.dtos.quote_response_dto import QuoteResponseDTO
from app.modules.quotes.dtos.quote_update_dto import UpdateQuoteDTO
from app.modules.quotes.entities.quote_entity import QuoteEntity
from app.modules.quotes.mappers.quote_mapper import QuoteMapper
from app.modules.quotes.repositories.quote_repository import QuoteRepository
from app.shared.dtos.page_dto import Page
from app.shared.dtos.page_params_dto import PageParams
from app.shared.exceptions.not_found_error import NotFoundError

logger = get_logger(__name__)


class QuoteService:
    """
    Service layer handling business logic for Quotes.
    """

    def __init__(self, repository: QuoteRepository) -> None:
        self.repository = repository

    async def list(self, params: PageParams) -> Page[QuoteResponseDTO]:
        entities = await self.repository.list(limit=params.limit, offset=params.offset)
        total = await self.repository.count()
        return Page(
            items=QuoteMapper.to_dto_list(entities),
            total=total,
            limit=params.limit,
            offset=params.offset,
        )

    async def get(self, quote_id: UUID) -> QuoteResponseDTO:
        return QuoteMapper.to_dto(await self._get_or_fail(quote_id))

    async def create(self, dto: CreateQuoteDTO) -> QuoteResponseDTO:
        entity = await self.repository.add(QuoteMapper.to_entity(dto))
        logger.info("quote created", extra={"quote_id": entity.id})
        return QuoteMapper.to_dto(entity)

    async def update(self, quote_id: UUID, dto: UpdateQuoteDTO) -> QuoteResponseDTO:
        entity = await self._get_or_fail(quote_id)
        entity = await self.repository.update(QuoteMapper.apply_update(entity, dto))
        logger.info("quote updated", extra={"quote_id": entity.id})
        return QuoteMapper.to_dto(entity)

    async def delete(self, quote_id: UUID) -> None:
        entity = await self._get_or_fail(quote_id)
        await self.repository.delete(entity)
        logger.info("quote deleted", extra={"quote_id": quote_id})

    async def _get_or_fail(self, quote_id: UUID) -> QuoteEntity:
        entity = await self.repository.get(quote_id)
        if entity is None:
            raise NotFoundError(f"Quote {quote_id} not found")
        return entity
