from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.quotes.entities.quote_entity import QuoteEntity
from app.modules.quotes.repositories.quote_repository import QuoteRepository


async def test_round_trip(db_session: AsyncSession) -> None:
    repository = QuoteRepository(db_session)

    created = await repository.add(QuoteEntity(text="Text", author="Author"))
    fetched = await repository.get(created.id)

    assert fetched is not None
    assert (fetched.text, fetched.author) == ("Text", "Author")
    assert await repository.count() == 1
