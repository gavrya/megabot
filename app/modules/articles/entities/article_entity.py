from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.entities.base_entity import Base, TimestampMixin


class ArticleEntity(Base, TimestampMixin):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
