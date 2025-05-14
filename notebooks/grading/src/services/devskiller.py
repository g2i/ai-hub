import os
import aiohttp
from src.types.devskiller import Assessment, EventPayload, DevSkillerResponse

class DevskillerService:
    def __init__(self):
        self.api_url = "https://api.devskiller.com"
        self.headers = {
            "Devskiller-Api-Key": os.getenv("DEVSKILLER_API_KEY"),
            "Content-Type": "application/vnd.devskiller.v2.hal+json",
            "Accept": "application/vnd.devskiller.v2.hal+json"
        }

    async def get_assessment(self, candidate_id: str, assessment_id: str) -> Assessment:
        url = f"{self.api_url}/candidates/{candidate_id}/assessments/{assessment_id}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
                response.raise_for_status()  # Raise exception for HTTP errors
                assessment_data = await response.json()
                return Assessment.model_validate(assessment_data)
    
    async def process_webhook_payload(self, payload: dict) -> EventPayload:
        """Process webhook payload from Devskiller and validate it"""
        return EventPayload.model_validate(payload)
    
    async def get_complete_data(self, payload: dict) -> DevSkillerResponse:
        """Process webhook payload and fetch assessment details in one go"""
        event_payload = await self.process_webhook_payload(payload)
        first_event = event_payload.root[0]
        assessment = await self.get_assessment(first_event.candidateId, first_event.assessmentId)
        
        return DevSkillerResponse(
            payload=event_payload,
            assessment=assessment
        )