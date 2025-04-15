from fastapi import FastAPI, Request, HTTPException, Response
import httpx
import os
import logging
import socket

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Docling API Proxy", 
              description="Proxy for Docling API with Railway private networking support")

# Get the bearer token from environment variable
DOCLING_API_TOKEN = os.getenv("DOCLING_API_TOKEN")

# Configure service using Railway private networking format
# IMPORTANT: For Railway private networking:
# 1. Must use http:// (not https://)
# 2. Must include the port 
# 3. Must use the format service-name.railway.internal
DOCLING_SERVICE_NAME = os.getenv("DOCLING_SERVICE_NAME", "docling-serve-cpu")
DOCLING_SERVICE_PORT = os.getenv("DOCLING_SERVICE_PORT", "5001")  # Docling serve default port is 5001
DOCLING_API_URL = os.getenv(
    "DOCLING_API_URL", 
    f"http://{DOCLING_SERVICE_NAME}.railway.internal:{DOCLING_SERVICE_PORT}"
)

# OAuth proxy support - similar to OpenShift pattern
USE_OAUTH_PROXY = os.getenv("USE_OAUTH_PROXY", "false").lower() == "true"

# Flag to skip auth for internal requests (set to True if Docling service doesn't need auth)
SKIP_AUTH_FOR_INTERNAL = os.getenv("SKIP_AUTH_FOR_INTERNAL", "false").lower() == "true"

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/info")
async def info():
    """Information about how to properly configure the server for Railway"""
    return {
        "service_info": {
            "name": "Docling API Proxy",
            "description": "Proxy service for Docling API with Railway private networking support"
        },
        "configuration": {
            "current_settings": {
                "DOCLING_SERVICE_NAME": DOCLING_SERVICE_NAME,
                "DOCLING_SERVICE_PORT": DOCLING_SERVICE_PORT,
                "DOCLING_API_URL": DOCLING_API_URL,
                "USE_OAUTH_PROXY": USE_OAUTH_PROXY,
                "SKIP_AUTH_FOR_INTERNAL": SKIP_AUTH_FOR_INTERNAL,
                "api_token_configured": DOCLING_API_TOKEN is not None
            },
            "railway_setup": {
                "fastapi_start_command": "uvicorn main:app --host :: --port $PORT",
                "ipv6_support": "Required for Railway private networking",
                "private_networking": "Enabled by default for all services in the same project"
            },
            "docling_setup": {
                "required_port": "Docling serve default port is 5001",
                "required_start_command": "Make sure Docling service is binding to :: for IPv6 support"
            }
        }
    }

@app.get("/diagnose")
async def diagnose():
    """Diagnostic endpoint to check connectivity to the Docling service"""
    results = {}
    
    # Check environment variables
    results["env"] = {
        "DOCLING_API_TOKEN": "configured" if DOCLING_API_TOKEN else "missing",
        "DOCLING_SERVICE_NAME": DOCLING_SERVICE_NAME,
        "DOCLING_SERVICE_PORT": DOCLING_SERVICE_PORT,
        "DOCLING_API_URL": DOCLING_API_URL,
        "USE_OAUTH_PROXY": USE_OAUTH_PROXY,
        "SKIP_AUTH_FOR_INTERNAL": SKIP_AUTH_FOR_INTERNAL
    }
    
    # Try to resolve the hostname using IPv6
    try:
        host = f"{DOCLING_SERVICE_NAME}.railway.internal"
        # Try IPv6 lookup
        addrinfo = socket.getaddrinfo(
            host, 
            int(DOCLING_SERVICE_PORT), 
            socket.AF_INET6, 
            socket.SOCK_STREAM
        )
        if addrinfo:
            addr = addrinfo[0][4]
            results["dns_lookup_ipv6"] = {
                "status": "success", 
                "ip": f"[{addr[0]}]:{addr[1]}"
            }
    except Exception as e:
        results["dns_lookup_ipv6"] = {"status": "failed", "error": str(e)}
    
    # Fallback to IPv4
    try:
        ip = socket.gethostbyname(host)
        results["dns_lookup_ipv4"] = {"status": "success", "ip": ip}
    except Exception as e:
        results["dns_lookup_ipv4"] = {"status": "failed", "error": str(e)}
    
    # Check environment info
    results["socket_info"] = {
        "IPv6 supported": socket.has_ipv6,
        "hostname": socket.gethostname(),
        "platform_info": os.uname() if hasattr(os, 'uname') else "Not available"
    }
    
    # Try alternate names with ports
    alternates = [
        f"http://{DOCLING_SERVICE_NAME}.railway.internal:{DOCLING_SERVICE_PORT}",
        # Alternate hostname format based on documentation
        f"http://{DOCLING_SERVICE_NAME}:{DOCLING_SERVICE_PORT}"
    ]
    
    # Try connections to various health endpoints and base URLs
    async with httpx.AsyncClient() as client:
        results["connection_tests"] = {}
        
        # First try without auth header
        for alt in alternates:
            # Test health endpoint without auth
            health_url = f"{alt}/health"
            try:
                logger.info(f"Testing connection without auth to: {health_url}")
                response = await client.get(health_url, timeout=5.0)
                results["connection_tests"][f"{health_url} (no auth)"] = {
                    "status": "success", 
                    "status_code": response.status_code,
                    "content": response.text[:100]  # First 100 chars
                }
            except Exception as e:
                results["connection_tests"][f"{health_url} (no auth)"] = {"status": "failed", "error": str(e)}
        
        # Now try with auth header if available
        if DOCLING_API_TOKEN:
            headers = {"Authorization": f"Bearer {DOCLING_API_TOKEN}"}
            for alt in alternates:
                health_url = f"{alt}/health"
                try:
                    logger.info(f"Testing connection with auth to: {health_url}")
                    response = await client.get(health_url, headers=headers, timeout=5.0)
                    results["connection_tests"][f"{health_url} (with auth)"] = {
                        "status": "success", 
                        "status_code": response.status_code,
                        "content": response.text[:100]  # First 100 chars
                    }
                except Exception as e:
                    results["connection_tests"][f"{health_url} (with auth)"] = {"status": "failed", "error": str(e)}
    
    return results

@app.post("/convert/file")
async def proxy_convert_file(request: Request):
    # Only check token if we're not skipping auth for internal requests
    if not SKIP_AUTH_FOR_INTERNAL and not DOCLING_API_TOKEN:
        raise HTTPException(status_code=500, detail="API token not configured")
    
    # Get raw request content instead of parsing as JSON
    content_type = request.headers.get("Content-Type", "")
    raw_body = await request.body()
    
    # Get the authorization header from the request
    auth_header = request.headers.get("Authorization", "")
    
    # Set up headers, preserving content-type
    headers = {"Content-Type": content_type}
    
    # Handle authentication based on configuration
    if USE_OAUTH_PROXY and auth_header:
        # Pass through the OAuth token from the request
        headers["Authorization"] = auth_header
        logger.info("Using OAuth token from request")
    elif not SKIP_AUTH_FOR_INTERNAL and DOCLING_API_TOKEN:
        # Use configured API token
        headers["Authorization"] = f"Bearer {DOCLING_API_TOKEN}"
        logger.info("Using configured API token")
    
    target_url = f"{DOCLING_API_URL}/v1alpha/convert/file"
    logger.info(f"Forwarding request to: {target_url}")
    
    # Forward the request as is
    async with httpx.AsyncClient() as client:
        try:
            # Configure HTTP client to use IPv6 if available
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

# Add support for OpenShift-style async convert endpoint
@app.post("/v1alpha/convert/source/async")
async def proxy_convert_source_async(request: Request):
    """Proxy endpoint for the OpenShift-style convert/source/async API"""
    # Get the authorization header from the request
    auth_header = request.headers.get("Authorization", "")
    
    # Get raw request content
    content_type = request.headers.get("Content-Type", "")
    raw_body = await request.body()
    
    # Set up headers, preserving content-type
    headers = {"Content-Type": content_type}
    
    # Handle authentication based on configuration
    if USE_OAUTH_PROXY and auth_header:
        # Pass through the OAuth token from the request
        headers["Authorization"] = auth_header
        logger.info("Using OAuth token from request for async conversion")
    elif not SKIP_AUTH_FOR_INTERNAL and DOCLING_API_TOKEN:
        # Use configured API token
        headers["Authorization"] = f"Bearer {DOCLING_API_TOKEN}"
        logger.info("Using configured API token for async conversion")
    
    target_url = f"{DOCLING_API_URL}/v1alpha/convert/source/async"
    logger.info(f"Forwarding async conversion request to: {target_url}")
    
    # Forward the request
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                target_url,
                content=raw_body,
                headers=headers,
                timeout=30.0
            )
            
            logger.info(f"Async conversion response received with status code: {response.status_code}")
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
        except Exception as e:
            error_message = f"Error with async conversion: {str(e)}"
            logger.error(error_message)
            raise HTTPException(
                status_code=500,
                detail=error_message
            )