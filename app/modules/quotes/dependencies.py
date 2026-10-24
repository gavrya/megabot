from typing import Annotated

from fastapi import Depends

from app.modules.quotes.repositories.quote_repository import QuoteRepository
from app.modules.quotes.services.quote_service import QuoteService
from app.shared.dependencies import SessionDep


def get_quote_service(session: SessionDep) -> QuoteService:
    """
    Dependency factory to initialize QuoteService with its repository dependency.
    """
    return QuoteService(QuoteRepository(session))


QuoteServiceDep = Annotated[QuoteService, Depends(get_quote_service)]
