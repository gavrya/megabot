from datetime import datetime

from pydantic import BaseModel


class ArticleResponseDTO(BaseModel):
    id: int
    title: str
    content: str
    created_at: datetime
    updated_at: datetime
