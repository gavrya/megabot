from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID

class CreateQuoteDTO(BaseModel):
    text: str = Field(..., min_length=1, description="Текст цитаты")
    author: str = Field(..., min_length=1, max_length=255, description="Автор цитаты")

class UpdateQuoteDTO(BaseModel):
    text: str | None = Field(None, min_length=1)
    author: str | None = Field(None, min_length=1, max_length=255)

class QuoteResponseDTO(BaseModel):
    id: UUID
    text: str
    author: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
