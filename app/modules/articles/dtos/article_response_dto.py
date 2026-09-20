from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ArticleResponseDTO(BaseModel):
    id: UUID
    title: str
    content: str
    created_at: datetime
    updated_at: datetime
