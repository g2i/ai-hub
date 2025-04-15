from fastapi import FastAPI, Request, HTTPException, Response
import httpx
import os

app = FastAPI()

DOCLING_API_TOKEN = os.getenv("DOCLING_API_TOKEN")


DOCLING_SERVICE_NAME = os.getenv("DOCLING_SERVICE_NAME", "docling-serve-cpu")
DOCLING_SERVICE_PORT = os.getenv("DOCLING_SERVICE_PORT", "")

DOCLING_API_URL = os.getenv(
    "DOCLING_API_URL", 
    f"http://{DOCLING_SERVICE_NAME}.railway.internal:{DOCLING_SERVICE_PORT}"
)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/convert/file")
async def proxy_convert_file(request: Request):
    if not DOCLING_API_TOKEN:
        raise HTTPException(status_code=500, detail="Proxy configuration error: API token missing")

    auth_header = request.headers.get("Authorization")
    
    expected_bearer = f"Bearer {DOCLING_API_TOKEN}"
    if not auth_header:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    if auth_header != expected_bearer:
        raise HTTPException(status_code=401, detail="Invalid authorization token")

    content_type = request.headers.get("Content-Type", "")
    raw_body = await request.body()
    
    headers = {"Content-Type": content_type}
    
    target_url = f"{DOCLING_API_URL}/v1alpha/convert/file"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                target_url,
                content=raw_body,
                headers=headers,
            )
            
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
        except Exception as e:
            error_message = f"Error communicating with Docling API at {target_url}: {str(e)}"
            # Optionally log the error_message if needed in the future
            raise HTTPException(
                status_code=500,
                detail="Error communicating with backend service"
            )