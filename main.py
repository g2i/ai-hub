"""
G2i AI Hub

This module provides the entry point for the FastAPI application.
"""
import logging
import logging.config
import os
from dotenv import load_dotenv

# Load environment variables first, before importing app
load_dotenv()

from app.app import app
from app.core.logging import DEFAULT_LOGGING_CONFIG
from app.core.logging import get_logger

# Configure logging
logging.config.dictConfig(DEFAULT_LOGGING_CONFIG)
logger = logging.getLogger("app.main")

# Check for critical environment variables
if not os.getenv("DOCLING_API_TOKEN"):
    logger.critical("DOCLING_API_TOKEN environment variable is not set.")
    logger.critical("The application will not function correctly without it.")
    logger.critical("Make sure the .env file exists and contains the required variables.")

# The app object is imported by the ASGI server
if __name__ == "__main__":
    # This section is only executed when running the module directly
    import uvicorn
    logger.info("Starting G2i AI Hub in development mode")
    uvicorn.run("app.app:app", host="0.0.0.0", port=8000, reload=True)