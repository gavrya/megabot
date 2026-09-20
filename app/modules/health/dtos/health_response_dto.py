from pydantic import BaseModel


class HealthResponseDTO(BaseModel):
    status: str
    service: str
    environment: str
    database: str
