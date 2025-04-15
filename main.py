from fastapi import FastAPI, Request, HTTPException, Response, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import JSONResponse
import httpx
import os
import secrets # For constant-time comparison

app = FastAPI()

# --- Configuration ---
DOCLING_API_TOKEN = os.getenv("DOCLING_API_TOKEN")
DOCLING_SERVICE_NAME = os.getenv("DOCLING_SERVICE_NAME", "docling-serve-cpu")
DOCLING_SERVICE_PORT = os.getenv("DOCLING_SERVICE_PORT", "")
DOCLING_API_URL = os.getenv(
    "DOCLING_API_URL", 
    f"http://{DOCLING_SERVICE_NAME}.railway.internal:{DOCLING_SERVICE_PORT}"
)
UI_USERNAME = os.getenv("UI_USERNAME")
UI_PASSWORD = os.getenv("UI_PASSWORD")

# --- Authentication ---

# Paths excluded from Bearer token auth (middleware)
# Note: UI paths are handled separately by the /ui endpoint's dependency
EXCLUDED_PATHS = ["/health", "/docs", "/openapi.json"]

# Basic Auth for UI
security = HTTPBasic()

def authenticate_basic_user(credentials: HTTPBasicCredentials = Depends(security)):
    if not UI_USERNAME or not UI_PASSWORD:
        print("CRITICAL: UI Basic Auth credentials not configured.")
        raise HTTPException(
            status_code=503, 
            detail="Service unavailable: Configuration error"
        )

    correct_username = secrets.compare_digest(credentials.username, UI_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, UI_PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"}, # Important for Basic Auth
        )
    return credentials.username

# Bearer Token Middleware (for non-excluded paths)
@app.middleware("http")
async def authenticate_bearer_request(request: Request, call_next):
    # Exclude exact paths, /ui, and /ui/ prefix
    if request.url.path in EXCLUDED_PATHS or request.url.path == "/ui" or request.url.path.startswith("/ui/"):
        response = await call_next(request)
        return response

    if not DOCLING_API_TOKEN:
        print("CRITICAL: Proxy configuration error: DOCLING_API_TOKEN not set.") 
        return JSONResponse(
            status_code=503, 
            content={"detail": "Service unavailable: Configuration error"}
        )

    auth_header = request.headers.get("Authorization")

    if not auth_header:
        return JSONResponse(
            status_code=401, 
            content={"detail": "Authorization header required"}
        )
    
    parts = auth_header.split(None, 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return JSONResponse(
            status_code=401,
            content={"detail": "Invalid Authorization header format. Expected 'Bearer <token>'"}
        )

    token = parts[1]
    # Use constant-time comparison for security
    if not secrets.compare_digest(token, DOCLING_API_TOKEN):
        return JSONResponse(
            status_code=401, 
            content={"detail": "Invalid authorization token"}
        )
    
    response = await call_next(request)
    return response

# --- Endpoints ---

@app.get("/health")
async def health():
    return {"status": "ok"}

# UI Proxy Endpoint Root (Basic Auth)
@app.get("/ui", include_in_schema=False) 
async def proxy_ui_root(request: Request, user: str = Depends(authenticate_basic_user)):
    target_url = f"{DOCLING_API_URL}/ui"
    async with httpx.AsyncClient() as client:
        try:
            fwd_headers = {h: v for h, v in request.headers.items() if h.lower() in ['accept', 'accept-language', 'user-agent']}
            backend_request = client.build_request(method=request.method, url=target_url, headers=fwd_headers, params=request.query_params)
            backend_response = await client.send(backend_request, stream=True)
            content = await backend_response.aread()
            response_headers = dict(backend_response.headers)
            return Response(content=content, status_code=backend_response.status_code, headers=response_headers)
        except httpx.ConnectError:
             raise HTTPException(status_code=503, detail="Cannot connect to the UI service.")
        except Exception as e:
            raise HTTPException(status_code=500, detail="Error proxying UI request.")

# UI Proxy Endpoint Subpaths (Basic Auth)
@app.get("/ui/{path:path}", include_in_schema=False)
async def proxy_ui_subpath(path: str, request: Request, user: str = Depends(authenticate_basic_user)):
    target_url = f"{DOCLING_API_URL}/ui/{path}"
    async with httpx.AsyncClient() as client:
        try:
            # Forward specific headers if needed, e.g., Accept
            fwd_headers = {h: v for h, v in request.headers.items() if h.lower() in ['accept', 'accept-language', 'user-agent']}
            
            backend_request = client.build_request(
                method=request.method, 
                url=target_url, 
                headers=fwd_headers, 
                params=request.query_params
            )
            backend_response = await client.send(backend_request, stream=True)
            
            # Read content for non-streaming or handle streaming response
            # Simple approach: Read all content (may not be suitable for large files)
            content = await backend_response.aread()
            response_headers = dict(backend_response.headers)
            # Ensure content-type is preserved
            if 'content-type' not in response_headers:
                 # Attempt to guess or set a default if needed
                 pass 

            return Response(
                content=content,
                status_code=backend_response.status_code,
                headers=response_headers
            )

        except httpx.ConnectError:
             raise HTTPException(status_code=503, detail="Cannot connect to the UI service.")
        except Exception as e:
            # Log the error server-side if needed
            # print(f"Error proxying UI: {e}")
            raise HTTPException(status_code=500, detail="Error proxying UI request.")

# API Proxy Endpoint (Bearer Auth via Middleware)
@app.post("/convert/file")
async def proxy_convert_file(request: Request):
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
                # Consider adding timeout=30.0 here for robustness
            )
            
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
        except Exception as e:
            error_message = f"Error communicating with Docling API at {target_url}: {str(e)}"
            raise HTTPException(
                status_code=500,
                detail="Error communicating with backend service"
            )