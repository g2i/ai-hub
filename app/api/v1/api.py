from fastapi import APIRouter

from app.api.v1.endpoints import health, document, agents, video

api_router = APIRouter()

# Health routes
api_router.include_router(
    health.router, 
    prefix="/health", 
    tags=["health"]
)

# Document processing routes
api_router.include_router(
    document.router, 
    prefix="/document", 
    tags=["document"]
)

# Agent routes (placeholder for future expansion)
api_router.include_router(
    agents.router, 
    prefix="/agents", 
    tags=["agents"]
)

api_router.include_router(
    video.router, 
    prefix="/video", 
    tags=["video"]
)

# Add additional route inclusions here as the application expands