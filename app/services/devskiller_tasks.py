import json
import re
from app.core.celery_app import celery_app
from app.services.devskiller import Devskiller, redis_client
import asyncio

def extract_ids_from_url(url):
    pattern = r"candidates/([^/]+)/detail/invitations/([^/]+)"
    match = re.search(pattern, url)
    if match:
        candidate_id = match.group(1)
        invitation_id = match.group(2)
        return candidate_id, invitation_id
    return None, None

@celery_app.task
def process_video_task(url: str):
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
    except Exception as e:
        redis_client.set(
            redis_key,
            json.dumps({"status": "error", "error": str(e)}),
            ex=3600
        )
        return {"status": "error", "error": str(e)} 