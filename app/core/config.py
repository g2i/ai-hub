import os
from pydantic_settings import BaseSettings
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Load .env file
load_dotenv()


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "G2i AI Hub"
    
    # API Authentication
    API_KEY: str = os.getenv("API_KEY", "")
    DOCLING_SERVICE_NAME: str = os.getenv("DOCLING_SERVICE_NAME", "docling-serve-cpu")
    DOCLING_SERVICE_PORT: str = os.getenv("DOCLING_SERVICE_PORT", "3000")
    DOCLING_API_URL: str = os.getenv(
        "DOCLING_API_URL", 
        f"http://{DOCLING_SERVICE_NAME}.railway.internal:{DOCLING_SERVICE_PORT}"
    )
    
    # Timeout settings (in seconds)
    DEFAULT_TIMEOUT: float = 300.0
    ASYNC_REQUEST_TIMEOUT: float = 30.0
    RESULT_FETCH_TIMEOUT: float = 60.0
    
    # API Documentation settings
    DOCS_URL: str = "/docs"
    REDOC_URL: str = "/redoc"
    OPENAPI_URL: str = "/openapi.json"
    
    # OpenAI settings
    OPENAI_API_KEY: Optional[str] = None
    
    # Devskiller settings
    DEVSKILLER_API_KEY: Optional[str] = None
    DEVSKILLER_USERNAME: Optional[str] = None
    DEVSKILLER_PASSWORD: Optional[str] = None
    
    # Browserbase settings
    BROWSERBASE_API_KEY: Optional[str] = None
    BROWSERBASE_PROJECT_ID: Optional[str] = None
    
    # Redis settings
    REDIS_CONN_STRING: Optional[str] = None
    
    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()