from fastapi import APIRouter, Query

from app.models.video.video import VideoResponse
from app.services.devskiller import Devskiller
router = APIRouter()

service = Devskiller()

@router.get("", response_model=VideoResponse)
async def get_video(url: str = Query(..., description="The DevSkiller video URL to process")):
    """
    Get video endpoint.
    
    Args:
        url: The DevSkiller video URL to process
        
    Returns:
        VideoResponse containing the processed video URL
    """

    video_url = await service.get_video_url(url)
    return VideoResponse(video_url=video_url)