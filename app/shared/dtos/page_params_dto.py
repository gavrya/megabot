from pydantic import BaseModel, Field


class PageParams(BaseModel):
    """Query parameters for paginated list endpoints."""

    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
