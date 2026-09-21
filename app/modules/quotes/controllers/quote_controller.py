from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, status, Depends

from app.modules.quotes.dtos.quote_dto import CreateQuoteDTO, UpdateQuoteDTO, QuoteResponseDTO
from app.modules.quotes.repositories.quote_repository import QuoteRepository
from app.modules.quotes.services.quote_service import QuoteService
from app.shared.dependencies import SessionDep
from app.shared.dtos.page_dto import Page
from app.shared.dtos.page_params_dto import PageParams


def get_quote_service(session: SessionDep) -> QuoteService:
    return QuoteService(QuoteRepository(session))


QuoteServiceDep = Annotated[QuoteService, Depends(get_quote_service)]

router = APIRouter()


@router.get("", response_model=Page[QuoteResponseDTO])
async def list_quotes(params: PageParams, service: QuoteServiceDep) -> Page[QuoteResponseDTO]:
    return await service.list(params)


@router.get("/{quote_id}", response_model=QuoteResponseDTO)
async def get_quote(quote_id: UUID, service: QuoteServiceDep) -> QuoteResponseDTO:
    return await service.get(quote_id)


@router.post("", response_model=QuoteResponseDTO, status_code=status.HTTP_201_CREATED)
async def create_quote(dto: CreateQuoteDTO, service: QuoteServiceDep) -> QuoteResponseDTO:
    return await service.create(dto)


@router.put("/{quote_id}", response_model=QuoteResponseDTO)
async def update_quote(quote_id: UUID, dto: UpdateQuoteDTO, service: QuoteServiceDep) -> QuoteResponseDTO:
    return await service.update(quote_id, dto)


@router.delete("/{quote_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quote(quote_id: UUID, service: QuoteServiceDep) -> None:
    await service.delete(quote_id)
