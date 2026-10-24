from app.modules.quotes.dtos.quote_create_dto import CreateQuoteDTO
from app.modules.quotes.dtos.quote_response_dto import QuoteResponseDTO
from app.modules.quotes.dtos.quote_update_dto import UpdateQuoteDTO
from app.modules.quotes.entities.quote_entity import QuoteEntity


class QuoteMapper:
    """
    Mapper class to convert between Quote DTOs and Quote Entity.
    """

    @staticmethod
    def to_entity(dto: CreateQuoteDTO) -> QuoteEntity:
        return QuoteEntity(text=dto.text, author=dto.author)

    @staticmethod
    def to_dto(entity: QuoteEntity) -> QuoteResponseDTO:
        return QuoteResponseDTO.model_validate(entity)

    @staticmethod
    def to_dto_list(entities: list[QuoteEntity]) -> list[QuoteResponseDTO]:
        return [QuoteMapper.to_dto(entity) for entity in entities]

    @staticmethod
    def apply_update(entity: QuoteEntity, dto: UpdateQuoteDTO) -> QuoteEntity:
        if dto.text is not None:
            entity.text = dto.text
        if dto.author is not None:
            entity.author = dto.author
        return entity
