from fastapi import APIRouter, HTTPException, BackgroundTasks
import json

from app.services.devskiller import redis_client
from app.services.devskiller_tasks import update_cookies_task

router = APIRouter()

STATUS_KEY = "devskiller_cookies_status"
LAST_UPDATED_KEY = "devskiller_cookies_last_updated"
ERROR_KEY = "devskiller_cookies_error"

@router.post("/refresh", response_model=dict)
@router.get("/refresh", response_model=dict)  # Allow GET for convenience
def refresh_cookies(background_tasks: BackgroundTasks):
    """Trigger a background task to refresh DevSkiller cookies.

    The task is executed asynchronously via Celery. The endpoint returns
    immediately with a *processing* status so that callers are not blocked
    while the cookies are being refreshed.
    """
    # Initialise status in Redis so consumers can poll for progress
    # Blocking Redis operations are safe here since this function runs in FastAPI's threadpool
    redis_client.set(STATUS_KEY, "processing", ex=172800)
    redis_client.delete(LAST_UPDATED_KEY)
    # Enqueue Celery task in background (after response is returned)
    background_tasks.add_task(update_cookies_task.delay)
    return {"status": "processing"}

# Using sync function to play safe with blocking I/O

@router.get("/status", response_model=dict)
def get_refresh_status():
    """Return the latest cookie refresh status."""
    status = redis_client.get(STATUS_KEY)
    if not status:
        raise HTTPException(status_code=404, detail="No cookie refresh status found")
    last_updated = redis_client.get(LAST_UPDATED_KEY)
    error_msg = redis_client.get(ERROR_KEY)
    return {
        "status": status.decode() if isinstance(status, (bytes, bytearray)) else status,
        "last_updated": (
            last_updated.decode() if isinstance(last_updated, (bytes, bytearray)) else last_updated
        ),
        "error": (
            error_msg.decode() if isinstance(error_msg, (bytes, bytearray)) else error_msg
        ),
    } 