from pydantic import BaseModel


class VideoResponse(BaseModel):
    """Video response model."""
    video_url: str