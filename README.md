# G2i AI Hub

A secure, extensible platform for AI services including document processing, agents, and more. Built with FastAPI to provide a scalable architecture for AI-powered features.

## Features

- **Document Processing:** Extract structured content from PDFs, Word documents, and more
- **AI Agents:** (Coming Soon) Autonomous agents for specialized tasks
- **Processing Chains:** (Coming Soon) Multi-step AI workflows
- **Knowledge Indexing:** (Coming Soon) Lemma and concept indexing

## Getting Started

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd api-proxy

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env to add your DOCLING_API_TOKEN
```

### Running

```bash
# Run the development server
python main.py
```

## Environment Configuration

Create a `.env` file with these variables:

```
# Required for document processing endpoints
DOCLING_API_TOKEN=your_api_token_here

# Optional (defaults shown)
DOCLING_API_URL=http://docling-serve-cpu.railway.internal:3000
DOCLING_SERVICE_NAME=docling-serve-cpu
DOCLING_SERVICE_PORT=3000
```

## API Reference

Base URL: `https://ai.g2i.co/api/v1`

### Public Endpoints (No Authentication)

- **Health Check:** `GET /health` - Verify the service is running
- **API Documentation:** `GET /docs` - Interactive API documentation
- **Agents (Coming Soon):** `GET /agents` - List available AI agents

### Authenticated Endpoints (Bearer Token Required)

All document processing endpoints require authentication with:
```
Authorization: Bearer <api_token>
```

#### Document Processing

- **Convert URL:** `POST /document/convert/source` - Process documents from URLs
- **Convert File:** `POST /document/convert/file` - Process uploaded document files
- **Async Processing:** `POST /document/convert/source/async` - Start async document conversion
- **Check Status:** `GET /document/status/poll/{task_id}?wait={seconds}` - Poll for status updates
- **Get Results:** `GET /document/result/{task_id}` - Retrieve conversion results

## Usage Examples

### Document Processing (Authenticated)

```bash
# Process a document from URL
curl -X 'POST' \
  'https://ai.g2i.co/api/v1/document/convert/source' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <api_token>' \
  -d '{
    "http_sources": [{"url": "https://arxiv.org/pdf/2206.01062.pdf"}],
    "options": {
      "to_formats": ["json"],
      "from_formats": ["pdf"],
      "image_export_mode": "embedded",
      "do_ocr": true
    }
  }' \
  --output 'output.zip'
```

### Agents API (No Authentication)

```bash
# List available agents
curl -X 'GET' 'https://ai.g2i.co/api/v1/agents'
```

## Document Processing Options

| Option | Description | Default |
|--------|-------------|---------|
| `to_formats` | Output formats (json, md, html, text, doctags) | ["md"] |
| `from_formats` | Input formats to process | ["pdf"] |
| `image_export_mode` | How to handle images (embedded, placeholder, referenced) | "embedded" |
| `do_ocr` | Enable OCR for images | true |
| `ocr_engine` | OCR engine to use (easyocr, rapidocr, tesseract) | "easyocr" |
| `pdf_backend` | PDF parsing backend | "dlparse_v4" |
| `return_as_file` | Return as ZIP file instead of JSON | false |

For a complete list of options, see the API documentation.

## Project Structure

```
app/
├── api/              # API routes by version
├── core/             # Configuration and utilities
├── middleware/       # Authentication middleware
├── models/           # Data models/schemas
├── services/         # Service integrations
├── utils/            # Utility functions
└── app.py            # Application entry point
```

## Deployment

The application uses Railway Nixpacks for deployment. Configuration is in `railway.json`.