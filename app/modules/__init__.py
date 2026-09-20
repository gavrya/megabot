"""Module registry.

Importing every module's entities here keeps `Base.metadata` complete, which is what
Alembic autogenerate inspects. Add one line per new module.
"""

from app.modules.articles.entities import article_entity

__all__ = ["article_entity"]
