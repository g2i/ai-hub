from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = "ok"
    service: str = "G2i AI Hub"