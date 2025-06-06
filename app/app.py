from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.middleware.auth import authenticate_request
from app.api.v1.api import api_router
from app.core.logging import get_logger

logger = get_logger("app.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Schedule cookie update task to run in background after startup
    # This prevents blocking the event loop during app initialization
    from app.services.devskiller_tasks import update_cookies_task
    
    logger.info("Scheduling initial DevSkiller cookie update...")
    # Queue the task to Celery - this returns immediately
    update_cookies_task.delay()
    
    yield
    # Cleanup if needed
    logger.info("Shutting down...")
    
def create_application() -> FastAPI:
    """
    Initialize and configure the FastAPI application.
    """
    # Log configuration information
    logger.info(f"Starting {settings.PROJECT_NAME}")
    
    # Only log a warning about missing API key at startup, but don't prevent the app from starting
    if not settings.API_KEY:
        logger.warning("No API_KEY configured. API endpoints will return 503 errors.")
    else:
        logger.info("API Key configured successfully")
    
    logger.info(f"API URL: {settings.DOCLING_API_URL}")
    
    application = FastAPI(
        title=settings.PROJECT_NAME,
        description="AI Hub providing document processing and AI services",
        version="0.1.0",
        docs_url=settings.DOCS_URL,
        redoc_url=settings.REDOC_URL,
        openapi_url=settings.OPENAPI_URL,
        lifespan=lifespan,
    )
    
    # Add CORS middleware
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, limit this to specific origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add authentication middleware
    application.middleware("http")(authenticate_request)
    
    # Include API router
    application.include_router(api_router, prefix=settings.API_V1_STR)
    
    # Add simple welcome message at root
    @application.get("/")
    async def root():
        """Root endpoint that redirects to documentation"""
        return {"message": f"Welcome to {settings.PROJECT_NAME}. See /docs for API documentation."}
    
    return application


app = create_application()