from uuid import UUID
from fastapi import APIRouter, status

from app.modules.quotes.dtos.quote_dto import CreateQuoteDTO, UpdateQuoteDTO, QuoteResponseDTO
from app.modules.quotes.dependencies import QuoteServiceDep
from app.shared.dtos.page_dto import Page
from app.shared.dtos.page_params_dto import PageParams

router = APIRouter()


@router.get("", response_model=Page[QuoteResponseDTO])
async def list_quotes(params: PageParams, service: QuoteServiceDep) -> Page[QuoteResponseDTO]:
    """
    Get a paginated list of quotes.
    """
    return await service.list(params)


@router.get("/{quote_id}", response_model=QuoteResponseDTO)
async def get_quote(quote_id: UUID, service: QuoteServiceDep) -> QuoteResponseDTO:
    """
    Get a specific quote by its UUID.
    """
    return await service.get(quote_id)


@router.post("", response_model=QuoteResponseDTO, status_code=status.HTTP_201_CREATED)
async def create_quote(dto: CreateQuoteDTO, service: QuoteServiceDep) -> QuoteResponseDTO:
    """
    Create a new quote.
    """
    return await service.create(dto)


@router.put("/{quote_id}", response_model=QuoteResponseDTO)
async def update_quote(quote_id: UUID, dto: UpdateQuoteDTO, service: QuoteServiceDep) -> QuoteResponseDTO:
    """
    Update an existing quote by its UUID.
    """
    return await service.update(quote_id, dto)


@router.delete("/{quote_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quote(quote_id: UUID, service: QuoteServiceDep) -> None:
    """
    Delete a quote by its UUID.
    """
    await service.delete(quote_id)
