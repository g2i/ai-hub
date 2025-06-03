import json
import re
from app.core.celery_app import celery_app
from app.services.devskiller import Devskiller, redis_client
import asyncio
from datetime import datetime, timezone
from celery.exceptions import SoftTimeLimitExceeded
import logging

logger = logging.getLogger(__name__)

def extract_ids_from_url(url):
    pattern = r"candidates/([^/]+)/detail/invitations/([^/]+)"
    match = re.search(pattern, url)
    if match:
        candidate_id = match.group(1)
        invitation_id = match.group(2)
        return candidate_id, invitation_id
    return None, None

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_video_task(self, url: str):
    candidate_id, invitation_id = extract_ids_from_url(url)
    if not candidate_id or not invitation_id:
        return {"status": "error", "error": "Invalid Devskiller URL format"}
    redis_key = f"video:{candidate_id}:{invitation_id}"
    try:
        service = Devskiller()
        # Run the async method in a new event loop
        result = asyncio.run(service.get_video_url(url))
        redis_client.set(
            redis_key,
            json.dumps({"status": "complete", "url": result}),
            ex=3600
        )
        return {"status": "complete", "url": result}
    except SoftTimeLimitExceeded:
        # Task took too long
        error_msg = "Task timed out after 4 minutes"
        redis_client.set(
            redis_key,
            json.dumps({"status": "error", "error": error_msg}),
            ex=3600
        )
        return {"status": "error", "error": error_msg}
    except Exception as e:
        # Retry on failure
        logger.error(f"Error processing video for {url}: {str(e)}")
        try:
            self.retry(exc=e)
        except self.MaxRetriesExceededError:
            redis_client.set(
                redis_key,
                json.dumps({"status": "error", "error": f"Max retries exceeded: {str(e)}"}),
                ex=3600
            )
            return {"status": "error", "error": f"Max retries exceeded: {str(e)}"}

@celery_app.task(bind=True, max_retries=3, default_retry_delay=300)
def update_cookies_task(self):
    """Background task to refresh DevSkiller cookies.

    A status object is stored in Redis under the key ``devskiller_cookies_status`` so
    other services can determine the current state of the cookie refresh process.
    The object has the structure:
    {
        "status": "processing" | "complete" | "error",
        "last_updated": <ISO8601 timestamp> | null,
        "error": <error message> | null
    }
    """
    STATUS_KEY = "devskiller_cookies_status"
    LAST_UPDATED_KEY = "devskiller_cookies_last_updated"
    ERROR_KEY = "devskiller_cookies_error"

    # Mark processing state and clear previous timestamp
    redis_client.set(STATUS_KEY, "processing", ex=172800)
    redis_client.delete(LAST_UPDATED_KEY)
    redis_client.delete(ERROR_KEY)

    try:
        service = Devskiller()
        # Run the async method in a new event loop
        asyncio.run(service.update_cookies())

        # On success, record completion time in UTC ISO-8601 format
        now_iso = datetime.now(timezone.utc).isoformat()
        redis_client.set(STATUS_KEY, "complete", ex=172800)
        redis_client.set(LAST_UPDATED_KEY, now_iso, ex=172800)
        redis_client.delete(ERROR_KEY)
        logger.info(f"Successfully updated DevSkiller cookies at {now_iso}")
        return {"status": "complete", "last_updated": now_iso}

    except SoftTimeLimitExceeded:
        # Task took too long
        error_msg = "Cookie update timed out after 4 minutes"
        logger.error(error_msg)
        redis_client.set(STATUS_KEY, "error", ex=172800)
        redis_client.set(ERROR_KEY, error_msg, ex=172800)
        return {"status": "error", "error": error_msg}
    except Exception as e:
        # Retry on failure
        logger.error(f"Error updating cookies: {str(e)}")
        try:
            self.retry(exc=e)
        except self.MaxRetriesExceededError:
            redis_client.set(STATUS_KEY, "error", ex=172800)
            redis_client.set(ERROR_KEY, f"Max retries exceeded: {str(e)}", ex=172800)
            return {"status": "error", "error": f"Max retries exceeded: {str(e)}"} 