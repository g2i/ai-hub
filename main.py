from fastapi import FastAPI, Request, HTTPException, Response
import httpx
import os
import logging
import socket

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Get the bearer token from environment variable
DOCLING_API_TOKEN = os.getenv("DOCLING_API_TOKEN")

# Configure service using Railway private networking format
# IMPORTANT: Must use http:// (not https://) and include port
DOCLING_SERVICE_NAME = os.getenv("DOCLING_SERVICE_NAME", "docling-serve-cpu")
DOCLING_SERVICE_PORT = os.getenv("DOCLING_SERVICE_PORT", "5001")  # Docling serve default port is 5001
DOCLING_API_URL = os.getenv(
    "DOCLING_API_URL", 
    f"http://{DOCLING_SERVICE_NAME}.railway.internal:{DOCLING_SERVICE_PORT}"
)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/diagnose")
async def diagnose():
    """Diagnostic endpoint to check connectivity to the Docling service"""
    results = {}
    
    # Check environment variables
    results["env"] = {
        "DOCLING_API_TOKEN": "configured" if DOCLING_API_TOKEN else "missing",
        "DOCLING_SERVICE_NAME": DOCLING_SERVICE_NAME,
        "DOCLING_SERVICE_PORT": DOCLING_SERVICE_PORT,
        "DOCLING_API_URL": DOCLING_API_URL
    }
    
    # Try to resolve the hostname
    try:
        host = f"{DOCLING_SERVICE_NAME}.railway.internal"
        ip = socket.gethostbyname(host)
        results["dns_lookup"] = {"status": "success", "ip": ip}
    except Exception as e:
        results["dns_lookup"] = {"status": "failed", "error": str(e)}
    
    # Try alternate names with ports
    alternates = [
        f"http://{DOCLING_SERVICE_NAME}.railway.internal:{DOCLING_SERVICE_PORT}",
        f"http://{DOCLING_SERVICE_NAME}.railway.internal:5001",
        f"http://{DOCLING_SERVICE_NAME}:{DOCLING_SERVICE_PORT}"
    ]
    
    # Try connections to various health endpoints and base URLs
    async with httpx.AsyncClient() as client:
        results["connection_tests"] = {}
        for alt in alternates:
            # Test health endpoint
            health_url = f"{alt}/health"
            try:
                logger.info(f"Testing connection to: {health_url}")
                response = await client.get(health_url, timeout=5.0)
                results["connection_tests"][health_url] = {
                    "status": "success", 
                    "status_code": response.status_code,
                    "content": response.text[:100]  # First 100 chars
                }
            except Exception as e:
                results["connection_tests"][health_url] = {"status": "failed", "error": str(e)}
            
            # Test base URL
            try:
                logger.info(f"Testing connection to base URL: {alt}")
                response = await client.get(alt, timeout=5.0)
                results["connection_tests"][alt] = {
                    "status": "success", 
                    "status_code": response.status_code,
                    "content": response.text[:100]  # First 100 chars
                }
            except Exception as e:
                results["connection_tests"][alt] = {"status": "failed", "error": str(e)}
    
    return results

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