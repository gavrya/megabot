from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.entities.base_entity import Base
from app.shared.entities.timestamp_mixin import TimestampMixin
from app.shared.entities.uuid_primary_key_mixin import UuidPrimaryKeyMixin


class ArticleEntity(UuidPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "articles"

    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
