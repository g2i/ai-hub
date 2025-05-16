from fastapi import APIRouter, Query, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
import json
import re

from app.models.video.video import VideoResponse
from app.services.devskiller import Devskiller, redis_client

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

# Store task result in Redis when done
async def process_and_store(url: str, redis_key: str):
    try:
        service = Devskiller()
        result = await service.get_video_url(url)
        # Store in Redis with 1-hour expiration
        redis_client.set(
            redis_key, 
            json.dumps({"status": "complete", "url": result}),
            ex=3600
        )
    except Exception as e:
        redis_client.set(
            redis_key,
            json.dumps({"status": "error", "error": str(e)}),
            ex=3600
        )

@router.get("", response_model=dict)
async def get_video(
    url: str = Query(..., description="The DevSkiller video URL to process"),
    background_tasks: BackgroundTasks = None
):
    """
    Start video processing in background.
    
    Args:
        url: The DevSkiller video URL to process
        
    Returns:
        Status and IDs for checking results
    """
    # Extract candidate and invitation IDs from URL
    candidate_id, invitation_id = extract_ids_from_url(url)
    
    if not candidate_id or not invitation_id:
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid Devskiller URL format"}
        )
    
    # Create Redis key from the IDs
    redis_key = f"video:{candidate_id}:{invitation_id}"
    
    # Store initial processing status in Redis
    redis_client.set(
        redis_key, 
        json.dumps({"status": "processing"}),
        ex=3600
    )
    
    # Start the task in the background and return immediately
    background_tasks.add_task(process_and_store, url, redis_key)
    
    # Return the IDs for checking status later
    return {
        "status": "processing", 
        "candidate_id": candidate_id, 
        "invitation_id": invitation_id
    }

@router.get("/status/{candidate_id}/{invitation_id}", response_model=dict)
async def get_task_status(candidate_id: str, invitation_id: str):
    """
    Check the status of a video processing task.
    
    Args:
        candidate_id: The candidate ID from the URL
        invitation_id: The invitation ID from the URL
        
    Returns:
        Task status and URL if complete
    """
    # Get the task result from Redis
    redis_key = f"video:{candidate_id}:{invitation_id}"
    result = redis_client.get(redis_key)
    
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Return the decoded result
    return json.loads(result)