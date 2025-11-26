from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("app.middleware.auth")

# Paths that require API token authentication
AUTH_REQUIRED_PREFIXES = [
    # All API v1 endpoints require authentication by default
    settings.API_V1_STR,
]

# Paths that explicitly don't require authentication
AUTH_EXCLUDED_PATHS = [
    "/health",
    f"{settings.API_V1_STR}/health",
]

# Exact paths that don't require authentication (not prefixes)
AUTH_EXCLUDED_EXACT_PATHS = [
    "/",  # Root path only
]

async def authenticate_request(request: Request, call_next):
    """
    Middleware that authenticates API requests using the configured token.
    
    Only endpoints that match AUTH_REQUIRED_PREFIXES require authentication.
    Paths in AUTH_EXCLUDED_PATHS always bypass authentication.
    """
    path = request.url.path
    logger.debug(f"Auth middleware processing: {path}")
    
    # Check if the exact path is excluded
    if path in AUTH_EXCLUDED_EXACT_PATHS:
        logger.debug(f"Path {path} is excluded from auth (exact match)")
        response = await call_next(request)
        return response
    
    # Check if the path is explicitly excluded from authentication
    for excluded_path in AUTH_EXCLUDED_PATHS:
        if excluded_path and path.startswith(excluded_path):
            logger.debug(f"Path {path} is excluded from auth (matches {excluded_path})")
            response = await call_next(request)
            return response
    
    # Check if the path requires authentication
    requires_auth = False
    for prefix in AUTH_REQUIRED_PREFIXES:
        if path.startswith(prefix):
            requires_auth = True
            logger.debug(f"Path {path} requires auth (matches {prefix})")
            break
    
    # If the path doesn't require authentication, continue
    if not requires_auth:
        logger.debug(f"Path {path} does not require auth")
        response = await call_next(request)
        return response
    
    # Path requires authentication, so verify API key configuration
    if not settings.API_KEY:
        logger.critical("Proxy configuration error: API_KEY not set.")
        logger.critical("Make sure environment variables are properly loaded from .env file.")
        return JSONResponse(
            status_code=503, 
            content={
                "detail": "Service unavailable: Configuration error - API key not set", 
                "message": "The API key is not configured. Please check the server configuration."
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
    if token != settings.API_KEY:
        logger.warning("Authentication attempt with invalid token")
        return JSONResponse(
            status_code=401, 
            content={"detail": "Invalid authorization token"}
        )
    
    # Token is valid, continue with request
    response = await call_next(request)
    return response