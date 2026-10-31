from app.modules.quotes.entities.quote_entity import QuoteEntity
from app.modules.quotes.repositories.quote_repository import QuoteRepository
from app.shared.repositories.base_repository import BaseRepository


def test_is_bound_to_quote_entity() -> None:
    assert issubclass(QuoteRepository, BaseRepository)
    assert QuoteRepository.model is QuoteEntity
