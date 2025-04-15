# Docling API Proxy

This API proxy provides a secure interface to the Docling document processing service. It handles authentication and forwards requests to the underlying Docling Serve API.

## API Authentication

All API endpoints (except `/health`, `/docs`, and `/openapi.json`) require authentication using a Bearer token:

```
Authorization: Bearer <api_token>
```

## Available Endpoints

### Health Check

```
GET /health
```

Returns a simple status check to verify the proxy is running.

### Document Processing

#### Convert from URL

```
POST /convert/source
```

Process documents from URLs.

#### Convert from File

```
POST /convert/file
```

Process uploaded document files.

### Asynchronous Processing

For processing large documents or batch processing, use the asynchronous endpoints:

#### Start Async Processing

```
POST /convert/source/async
```

Initiates asynchronous processing and returns a task ID.

#### Check Task Status

```
GET /status/poll/{task_id}?wait={seconds}
```

Poll for task status. The optional `wait` parameter specifies how long to wait (in seconds) for a status change.

#### Get Task Result

```
GET /result/{task_id}
```

Retrieve the result of a completed task.

## Usage Examples

### Processing a Document from URL

```bash
curl -X 'POST' \
  'https://docling.g2i.co/convert/source' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -H 'authorization: Bearer <api_token>' \
  -d '{
    "http_sources": [
      {"url": "https://arxiv.org/pdf/2206.01062.pdf"}
    ],
    "options": {
      "to_formats": ["json"],
      "from_formats": ["pdf"],
      "image_export_mode": "embedded",
      "do_ocr": true,
      "force_ocr": false,
      "ocr_engine": "rapidocr",
      "ocr_lang": ["en"],
      "pdf_backend": "dlparse_v4",
      "table_mode": "fast",
      "abort_on_error": true,
      "return_as_file": true,
      "do_table_structure": true,
      "include_images": false,
      "images_scale": 2.0,
      "do_code_enrichment": false,
      "do_formula_enrichment": false,
      "do_picture_description": false
    }
  }' \
  --output '/path/to/output.zip'
```

### Uploading and Processing a File

```bash
curl -X 'POST' \
  'https://docling.g2i.co/convert/file' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -H 'authorization: Bearer <api_token>' \
  -F 'do_code_enrichment=false' \
  -F 'ocr_engine=rapidocr' \
  -F 'images_scale=2' \
  -F 'pdf_backend=dlparse_v4' \
  -F 'do_picture_description=false' \
  -F 'from_formats=pdf' \
  -F 'image_export_mode=embedded' \
  -F 'do_ocr=true' \
  -F 'do_table_structure=true' \
  -F 'ocr_lang=en' \
  -F 'include_images=false' \
  -F 'do_formula_enrichment=false' \
  -F 'table_mode=fast' \
  -F 'files=@/path/to/document.pdf;type=application/pdf' \
  -F 'abort_on_error=true' \
  -F 'return_as_file=true' \
  -F 'to_formats=json' \
  --output '/path/to/output.zip'
```

### Asynchronous Processing

```bash
# Start async processing
curl -X 'POST' \
  'https://docling.g2i.co/convert/source/async' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -H 'authorization: Bearer <api_token>' \
  -d '{
    "http_sources": [
      {"url": "https://arxiv.org/pdf/2206.01062.pdf"}
    ],
    "options": {
      "to_formats": ["json"],
      "image_export_mode": "embedded"
    }
  }'

# Response contains a task_id
# {
#   "task_id": "123e4567-e89b-12d3-a456-426614174000",
#   "task_status": "pending",
#   "task_position": 1
# }

# Check status (optional: wait for up to 5 seconds)
curl -X 'GET' \
  'https://docling.g2i.co/status/poll/123e4567-e89b-12d3-a456-426614174000?wait=5' \
  -H 'authorization: Bearer <api_token>'

# Get result when complete
curl -X 'GET' \
  'https://docling.g2i.co/result/123e4567-e89b-12d3-a456-426614174000' \
  -H 'authorization: Bearer <api_token>' \
  --output '/path/to/output.zip'
```

## Processing Options

| Option | Description | Default |
|--------|-------------|---------|
| `to_formats` | Output formats (json, md, html, text, doctags) | ["md"] |
| `from_formats` | Input formats to process | ["pdf"] |
| `image_export_mode` | How to handle images (embedded, placeholder, referenced) | "embedded" |
| `do_ocr` | Enable OCR for images | true |
| `force_ocr` | Replace existing text with OCR | false |
| `ocr_engine` | OCR engine to use (easyocr, rapidocr, tesseract) | "easyocr" |
| `ocr_lang` | Languages for OCR | ["en"] |
| `pdf_backend` | PDF parsing backend | "dlparse_v4" |
| `table_mode` | Table extraction mode (fast, accurate) | "fast" |
| `return_as_file` | Return as ZIP file instead of JSON | false |
| `do_table_structure` | Extract table structures | true |
| `include_images` | Extract images from document | true |
| `do_code_enrichment` | Enhance code block recognition | false |
| `do_formula_enrichment` | Extract mathematical formulas as LaTeX | false |
| `do_picture_classification` | Classify images in document | false |
| `do_picture_description` | Generate descriptions for images | false |

## Response Formats

When `return_as_file` is true or multiple documents are processed, the response is a ZIP file containing the processed documents.

Otherwise, the response includes document content in the requested formats, along with metadata about the processing.

JSON output includes full document structure with bounding box information for all document elements.