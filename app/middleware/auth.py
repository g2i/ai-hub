from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("app.middleware.auth")

# Paths that require API token authentication
AUTH_REQUIRED_PREFIXES = [
    # Document processing endpoints
    f"{settings.API_V1_STR}/document/",
    # Future protected endpoints can be added here
]

# Paths that explicitly don't require authentication
AUTH_EXCLUDED_PATHS = [
    "/health",
    settings.DOCS_URL,
    settings.OPENAPI_URL,
    settings.REDOC_URL,
    f"{settings.API_V1_STR}/health",
    # Agent endpoints temporarily excluded until authentication strategy is determined
    f"{settings.API_V1_STR}/agents",
]

async def authenticate_request(request: Request, call_next):
    """
    Middleware that authenticates API requests using the configured token.
    
    Only endpoints that match AUTH_REQUIRED_PREFIXES require authentication.
    Paths in AUTH_EXCLUDED_PATHS always bypass authentication.
    """
    path = request.url.path
    
    # Check if the path is explicitly excluded from authentication
    for excluded_path in AUTH_EXCLUDED_PATHS:
        if path.startswith(excluded_path):
            response = await call_next(request)
            return response
    
    # Check if the path requires authentication
    requires_auth = False
    for prefix in AUTH_REQUIRED_PREFIXES:
        if path.startswith(prefix):
            requires_auth = True
            break
    
    # If the path doesn't require authentication, continue
    if not requires_auth:
        response = await call_next(request)
        return response
    
    # Path requires authentication, so verify Docling API token configuration
    if not settings.DOCLING_API_TOKEN:
        logger.critical("Proxy configuration error: DOCLING_API_TOKEN not set.")
        logger.critical("Make sure environment variables are properly loaded from .env file.")
        return JSONResponse(
            status_code=503, 
            content={
                "detail": "Service unavailable: Configuration error - API token not set", 
                "message": "The API token is not configured. Please check the server configuration."
            }
        )

    # Check for Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return JSONResponse(
            status_code=401, 
            content={"detail": "Authorization header required"}
        )
    
    # Validate Authorization header format
    parts = auth_header.split(None, 1)  # Split on first whitespace
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return JSONResponse(
            status_code=401,
            content={"detail": "Invalid Authorization header format. Expected 'Bearer <token>'"}
        )

    # Validate token
    token = parts[1]
    if token != settings.DOCLING_API_TOKEN:
        logger.warning("Authentication attempt with invalid token")
        return JSONResponse(
            status_code=401, 
            content={"detail": "Invalid authorization token"}
        )
    
    # Token is valid, continue with request
    response = await call_next(request)
    return response