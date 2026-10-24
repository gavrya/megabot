from pydantic import BaseModel, ConfigDict, Field


class UpdateQuoteDTO(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    text: str | None = Field(None, min_length=1)
    author: str | None = Field(None, min_length=1, max_length=255)
