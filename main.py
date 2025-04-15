from fastapi import FastAPI, Request, HTTPException, Response
import httpx
import os
import logging
import socket
import urllib.parse

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

# Try direct IPv6 address if needed
USE_DIRECT_IPV6 = os.getenv("USE_DIRECT_IPV6", "false").lower() == "true"
IPV6_ADDRESS = os.getenv("IPV6_ADDRESS", "")

# Construct the API URL based on available information
if USE_DIRECT_IPV6 and IPV6_ADDRESS:
    # Format for direct IPv6 in URL: http://[IPv6]:port
    DOCLING_API_URL = f"http://[{IPV6_ADDRESS}]:{DOCLING_SERVICE_PORT}"
else:
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
                "USE_DIRECT_IPV6": USE_DIRECT_IPV6,
                "IPV6_ADDRESS": IPV6_ADDRESS if IPV6_ADDRESS else "Not set",
                "api_token_configured": DOCLING_API_TOKEN is not None
            },
            "railway_setup": {
                "fastapi_start_command": "uvicorn main:app --host :: --port $PORT",
                "ipv6_support": "Required for Railway private networking",
                "private_networking": "Enabled by default for all services in the same project"
            },
            "docling_setup": {
                "required_port": "Docling serve default port is 5001",
                "required_start_command": "Make sure Docling service is binding to :: for IPv6 support",
                "ipv6_binding": "The service must bind to IPv6 (::) to be reachable via the private network"
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
        "SKIP_AUTH_FOR_INTERNAL": SKIP_AUTH_FOR_INTERNAL,
        "USE_DIRECT_IPV6": USE_DIRECT_IPV6,
        "IPV6_ADDRESS": IPV6_ADDRESS if IPV6_ADDRESS else "Not set"
    }
    
    # Try to resolve the hostname using IPv6
    ipv6_address = None
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
            ipv6_address = addr[0]  # Save for potential direct connection testing
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
    
    # Try connections using various methods
    results["connection_tests"] = {}

    # Setup connection test URLs
    test_urls = [
        # Test domain-based URLs
        f"http://{DOCLING_SERVICE_NAME}.railway.internal:{DOCLING_SERVICE_PORT}/health",
        f"http://{DOCLING_SERVICE_NAME}:{DOCLING_SERVICE_PORT}/health",
    ]
    
    # Add direct IPv6 connection if we have an address
    if ipv6_address or IPV6_ADDRESS:
        addr_to_use = IPV6_ADDRESS if IPV6_ADDRESS else ipv6_address
        test_urls.append(f"http://[{addr_to_use}]:{DOCLING_SERVICE_PORT}/health")
    
    # Test basic socket connectivity first
    if ipv6_address:
        try:
            # Create a socket and try to connect directly
            s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            s.settimeout(2)  # 2 second timeout
            
            logger.info(f"Testing raw socket IPv6 connection to {ipv6_address}:{DOCLING_SERVICE_PORT}")
            s.connect((ipv6_address, int(DOCLING_SERVICE_PORT)))
            s.close()
            
            results["raw_socket_test"] = {
                "status": "success",
                "message": f"Successfully connected to {ipv6_address}:{DOCLING_SERVICE_PORT}"
            }
        except Exception as e:
            results["raw_socket_test"] = {
                "status": "failed",
                "error": str(e)
            }
    
    # Test connections with httpx
    async with httpx.AsyncClient() as client:
        # First try without auth header
        for url in test_urls:
            try:
                logger.info(f"Testing connection without auth to: {url}")
                response = await client.get(url, timeout=5.0)
                results["connection_tests"][f"{url} (no auth)"] = {
                    "status": "success", 
                    "status_code": response.status_code,
                    "content": response.text[:100]  # First 100 chars
                }
            except Exception as e:
                results["connection_tests"][f"{url} (no auth)"] = {"status": "failed", "error": str(e)}
        
        # Now try with auth header if available
        if DOCLING_API_TOKEN:
            headers = {"Authorization": f"Bearer {DOCLING_API_TOKEN}"}
            for url in test_urls:
                try:
                    logger.info(f"Testing connection with auth to: {url}")
                    response = await client.get(url, headers=headers, timeout=5.0)
                    results["connection_tests"][f"{url} (with auth)"] = {
                        "status": "success", 
                        "status_code": response.status_code,
                        "content": response.text[:100]  # First 100 chars
                    }
                except Exception as e:
                    results["connection_tests"][f"{url} (with auth)"] = {"status": "failed", "error": str(e)}
    
    # Provide recommendations based on results
    results["recommendations"] = {}
    
    # Check if we found an IPv6 address but couldn't connect
    if ipv6_address and all("failed" in v.get("status", "") for k, v in results["connection_tests"].items() if "with auth" in k):
        results["recommendations"]["ipv6_direct"] = {
            "action": "Try direct IPv6 connection",
            "instruction": f"Set USE_DIRECT_IPV6=true and IPV6_ADDRESS={ipv6_address} in your environment variables"
        }
    
    # If raw socket test failed, suggest checking if the service is listening on IPv6
    if results.get("raw_socket_test", {}).get("status") == "failed":
        results["recommendations"]["check_service"] = {
            "action": "Ensure Docling service is listening on IPv6",
            "instruction": "Configure the Docling service to bind to :: instead of 0.0.0.0 or localhost"
        }
    
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