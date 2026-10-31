from unittest.mock import Mock

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.quotes.dependencies import get_quote_service
from app.modules.quotes.repositories.quote_repository import QuoteRepository
from app.modules.quotes.services.quote_service import QuoteService


def test_wires_repository_to_session() -> None:
    session = Mock(spec=AsyncSession)

    service = get_quote_service(session)

    assert isinstance(service, QuoteService)
    assert isinstance(service.repository, QuoteRepository)
    assert service.repository.session is session
