from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import JSONResponse
import json
import re

from app.models.video.video import VideoResponse
from app.services.devskiller import redis_client
from app.services.devskiller_tasks import process_video_task

router = APIRouter()

# Extract candidate and invitation IDs from URL
def extract_ids_from_url(url):
    pattern = r"candidates/([^/]+)/detail/invitations/([^/]+)"
    match = re.search(pattern, url)
    if match:
        candidate_id = match.group(1)
        invitation_id = match.group(2)
        return candidate_id, invitation_id
    return None, None

@router.get("", response_model=dict)
async def get_video(
    url: str = Query(..., description="The DevSkiller video URL to process")
):
    """
    Start video processing as a Celery task.
    """
    candidate_id, invitation_id = extract_ids_from_url(url)
    if not candidate_id or not invitation_id:
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid Devskiller URL format"}
        )
    redis_key = f"video:{candidate_id}:{invitation_id}"
    # Store initial processing status in Redis
    redis_client.set(
        redis_key,
        json.dumps({"status": "processing"}),
        ex=3600
    )
    # Enqueue Celery task
    process_video_task.delay(url)
    return {
        "status": "processing",
        "candidate_id": candidate_id,
        "invitation_id": invitation_id
    }

@router.get("/status/{candidate_id}/{invitation_id}", response_model=dict)
async def get_task_status(candidate_id: str, invitation_id: str):
    redis_key = f"video:{candidate_id}:{invitation_id}"
    result = redis_client.get(redis_key)
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    return json.loads(result)