from app.core.logging import get_logger
from app.modules.articles.entities.article_entity import ArticleEntity
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)

ARTICLES = [
    {"title": "Welcome to megabot", "content": "This article was created by the seeder."},
    {"title": "Layered architecture", "content": "Controller -> Service -> Repository -> Entity."},
    {"title": "Async SQLAlchemy", "content": "Asyncpg driver with SQLAlchemy 2.0 ORM."},
]


async def run(session: AsyncSession) -> None:
    """Idempotent: inserts only the demo articles that are not present yet."""
    existing = await session.execute(
        select(ArticleEntity.title).where(
            ArticleEntity.title.in_([item["title"] for item in ARTICLES])
        )
    )
    known = set(existing.scalars().all())

    session.add_all(ArticleEntity(**item) for item in ARTICLES if item["title"] not in known)
    await session.flush()

    total = await session.execute(select(func.count()).select_from(ArticleEntity))
    logger.info("articles in table: %s", total.scalar_one())
