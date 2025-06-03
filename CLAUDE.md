# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the G2i AI Hub, a FastAPI-based service that provides a secure interface to the Docling document processing service and other AI services. It handles authentication and forwards document processing requests to the underlying Docling Serve API while providing a foundation for expanding to additional AI capabilities.

## Development Commands

### Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables (first time only)
cp .env.example .env
# Edit .env to add your DOCLING_API_TOKEN and other configuration

# Run the development server
python main.py

# Or using hypercorn directly
hypercorn app.app:app --reload --bind 0.0.0.0:8000
```

### Running Background Tasks with Celery

The application uses Celery for background tasks (video processing, DevSkiller cookie updates). You need to run Celery workers:

```bash
# Run Celery worker (required for background tasks)
celery -A app.core.celery_app worker --loglevel=info

# Run Celery Beat scheduler (for periodic tasks like cookie updates every 12 hours)
celery -A app.core.celery_app beat --loglevel=info

# Or run both together (development only)
celery -A app.core.celery_app worker --beat --loglevel=info
```

### Environment Variables

The following environment variables are required:

- `API_KEY`: Bearer token for authenticating API requests (e.g., "123")
- `DOCLING_API_URL`: (Optional) URL of the Docling Serve API (defaults to internal Railway service)
- `DOCLING_SERVICE_NAME`: (Optional) Name of the service (defaults to "docling-serve-cpu")
- `DOCLING_SERVICE_PORT`: (Optional) Port of the service (defaults to "3000")
- `REDIS_CONN_STRING`: Redis connection URL for Celery and caching
- `DEVSKILLER_USERNAME`: DevSkiller login email
- `DEVSKILLER_PASSWORD`: DevSkiller login password

These variables should be defined in a `.env` file in the project root.

### Deployment

This project is configured for deployment on Railway using Nixpacks. The deployment configuration is in `railway.json`.

## Architecture

The application follows a modular structure for better organization and expandability:

```
app/
├── api/              # API routes organized by version
│   └── v1/           # Version 1 of the API
│       ├── api.py    # Main router that includes all endpoint routers
│       └── endpoints/ # Individual endpoint modules
│           ├── agents.py    # AI agents endpoints
│           ├── document.py  # Document processing endpoints 
│           └── health.py    # Health check endpoint
├── core/             # Core application settings and utilities
│   ├── config.py     # Configuration settings
│   └── logging.py    # Logging configuration
├── middleware/       # Custom middleware components
│   └── auth.py       # Authentication middleware
├── models/           # Pydantic models/schemas
│   └── health.py     # Health response model
├── services/         # Business logic and external service integrations
│   └── docling.py    # Docling API service
├── utils/            # Utility functions
│   └── env.py        # Environment variable utilities
└── app.py            # Application factory and configuration
```

### Main Components:

1. **API Routers**: Organized by version and feature area
   - Health check (`/api/v1/health`)
   - Document processing endpoints:
     - Synchronous processing: `/api/v1/document/convert/file` and `/api/v1/document/convert/source`
     - Asynchronous processing: `/api/v1/document/convert/source/async`
     - Status polling: `/api/v1/document/status/poll/{task_id}`
     - Result retrieval: `/api/v1/document/result/{task_id}`
   - Agent capabilities (`/api/v1/agents`)
   - DevSkiller endpoints:
     - Cookie refresh: `POST /api/v1/devskiller/refresh` (triggers background update)
     - Cookie status: `GET /api/v1/devskiller/status` (check update status)
   - Video processing:
     - Submit video: `POST /api/v1/video/process`
     - Check status: `GET /api/v1/video/status/{candidate_id}/{invitation_id}`

2. **Authentication Middleware**: Validates all requests using Bearer token authentication
   - Header format: `Authorization: Bearer <API_KEY>`
   - Configure via `API_KEY` environment variable

3. **Service Modules**: Encapsulate interactions with external services
   - `DoclingService`: Handles communication with the Docling Serve API with configurable timeouts:
     - `DEFAULT_TIMEOUT`: 300 seconds for standard conversions
     - `ASYNC_REQUEST_TIMEOUT`: 30 seconds for async request initiation
     - `RESULT_FETCH_TIMEOUT`: 60 seconds for fetching results

4. **Models**: Pydantic models for request/response validation and documentation

5. **Environment Management**: Uses python-dotenv to load environment variables from .env file

This modular architecture makes it easy to add new API endpoints, integrate with additional services, and expand the application's capabilities without modifying existing code.