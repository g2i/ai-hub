from fastapi import FastAPI, Request, HTTPException
import httpx
import os

app = FastAPI()

# Get the bearer token from environment variable
DOCLING_API_TOKEN = os.getenv("DOCLING_API_TOKEN")

@app.post("/health")
async def health():
    return {"status": "ok"}

@app.post("/convert/file")
async def proxy_convert_file(request: Request):
    # Check if the token is configured
    if not DOCLING_API_TOKEN:
        raise HTTPException(status_code=500, detail="API token not configured")
    
    request_body = await request.json()
    
    # Set up headers with bearer token
    headers = {
        "Authorization": f"Bearer {DOCLING_API_TOKEN}"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://docling-serve-cpu.railway.internal/v1alpha/convert/file",
            json=request_body,
            headers=headers
        )
        
        return response.json()