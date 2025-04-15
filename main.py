from fastapi import FastAPI, Request, HTTPException, Response
import httpx
import os

app = FastAPI()

# Get the bearer token from environment variable
DOCLING_API_TOKEN = os.getenv("DOCLING_API_TOKEN")
# Use the Railway internal DNS name for the docling service
DOCLING_API_URL = os.getenv("DOCLING_API_URL", "http://docling-serve-cpu.railway.internal")

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
    
    # Forward the request as is
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{DOCLING_API_URL}/v1alpha/convert/file",
                content=raw_body,  # Use raw content instead of json
                headers=headers,
                timeout=30.0  # Add a timeout to prevent hanging requests
            )
            
            # Return the response with the same status code and headers
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
        except httpx.ConnectError as e:
            raise HTTPException(
                status_code=503,
                detail=f"Could not connect to Docling API: {str(e)}"
            )
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=504,
                detail="Request to Docling API timed out"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error communicating with Docling API: {str(e)}"
            )