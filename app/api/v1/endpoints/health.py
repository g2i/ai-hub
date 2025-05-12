from fastapi import APIRouter

from app.models.health import HealthResponse

router = APIRouter()


@router.get("", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns a simple status check to verify the API is running.
    """
    return HealthResponse()