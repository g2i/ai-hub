from fastapi import FastAPI, Request, HTTPException, Response
import httpx
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Get the bearer token from environment variable
DOCLING_API_TOKEN = os.getenv("DOCLING_API_TOKEN")
# Use the simple service name for Railway internal DNS
DOCLING_API_URL = os.getenv("DOCLING_API_URL", "http://docling-serve-cpu")

@app.post("/health")
async def health():
    return {"status": "ok"}

@app.post("/convert/file")
async def proxy_convert_file(request: Request):
    # Check if the token is configured
    if not DOCLING_API_TOKEN:
        raise HTTPException(status_code=500, detail="API token not configured")
    
    # Get raw request content instead of parsing as JSON
    content_type = request.headers.get("Content-Type", "")
    raw_body = await request.body()
    
    # Set up headers with bearer token and preserve content-type
    headers = {
        "Authorization": f"Bearer {DOCLING_API_TOKEN}",
        "Content-Type": content_type
    }
    
    target_url = f"{DOCLING_API_URL}/v1alpha/convert/file"
    logger.info(f"Forwarding request to: {target_url}")
    
    # Forward the request as is
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                target_url,
                content=raw_body,  # Use raw content instead of json
                headers=headers,
                timeout=30.0  # Add a timeout to prevent hanging requests
            )
            
            logger.info(f"Response received with status code: {response.status_code}")
            # Return the response with the same status code and headers
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
        except httpx.ConnectError as e:
            error_message = f"Could not connect to Docling API at {target_url}: {str(e)}"
            logger.error(error_message)
            raise HTTPException(
                status_code=503,
                detail=error_message
            )
        except httpx.TimeoutException:
            error_message = f"Request to Docling API at {target_url} timed out"
            logger.error(error_message)
            raise HTTPException(
                status_code=504,
                detail=error_message
            )
        except Exception as e:
            error_message = f"Error communicating with Docling API at {target_url}: {str(e)}"
            logger.error(error_message)
            raise HTTPException(
                status_code=500,
                detail=error_message
            )