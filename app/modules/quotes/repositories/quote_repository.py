from app.modules.quotes.entities.quote_entity import QuoteEntity
from app.shared.repositories.base_repository import BaseRepository


class QuoteRepository(BaseRepository[QuoteEntity]):
    """
    Repository for managing QuoteEntity database operations.
    Inherits all standard CRUD operations from BaseRepository.
    """

    model = QuoteEntity
