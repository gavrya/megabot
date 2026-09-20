from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ArticleCreateDTO(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)


class ArticleUpdateDTO(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)


class ArticleResponseDTO(BaseModel):
    id: int
    title: str
    content: str
    created_at: datetime
    updated_at: datetime
