import httpx
from fastapi import HTTPException, Request, Response
from typing import Optional

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("app.services.docling")

class DoclingService:
    """Service class for interacting with the Docling API."""
    
    @staticmethod
    async def proxy_request(
        request: Request, 
        endpoint: str, 
        method: str = "POST",
        timeout: Optional[float] = None,
        query_params: Optional[dict] = None
    ) -> Response:
        """
        Proxy a request to the Docling API.
        
        Args:
            request: The original FastAPI request
            endpoint: The Docling API endpoint path
            method: HTTP method (GET, POST, etc.)
            timeout: Request timeout in seconds
            query_params: Optional query parameters
            
        Returns:
            FastAPI Response containing the Docling API's response
        """
        if timeout is None:
            timeout = settings.DEFAULT_TIMEOUT
            
        target_url = f"{settings.DOCLING_API_URL}{endpoint}"
        if query_params:
            query_string = "&".join(f"{k}={v}" for k, v in query_params.items() if v is not None)
            if query_string:
                target_url = f"{target_url}?{query_string}"
        
        headers = {}
        content = None
        
        # For POST requests, get content body and headers
        if method == "POST":
            content_type = request.headers.get("Content-Type", "")
            content = await request.body()
            headers["Content-Type"] = content_type
            
        logger.info(f"Proxying {method} request to {target_url}")
        
        async with httpx.AsyncClient() as client:
            try:
                if method == "GET":
                    response = await client.get(
                        target_url,
                        headers=headers,
                        timeout=timeout
                    )
                elif method == "POST":
                    response = await client.post(
                        target_url,
                        content=content,
                        headers=headers,
                        timeout=timeout
                    )
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                return Response(
                    content=response.content,
                    status_code=response.status_code,
                    headers=dict(response.headers)
                )
                
            except Exception as e:
                logger.error(f"Error communicating with Docling API at {target_url}:", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail="Error communicating with backend service"
                )