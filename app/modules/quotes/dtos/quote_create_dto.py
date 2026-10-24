from pydantic import BaseModel, ConfigDict, Field


class CreateQuoteDTO(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    text: str = Field(min_length=1, description="Quote text")
    author: str = Field(min_length=1, max_length=255, description="Quote author")
