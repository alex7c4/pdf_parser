# PDF Parser

A web application that converts PDF documents to Markdown (or plain text) and generates AI-powered summaries.

## Features

- **Multiple Parsing Options**:
  - Google Gemini Flash (Markdown output) - Default
  - Mistral OCR (Markdown output)
  - PyPDF (Plain text output)

- **AI-Powered Summarization**: Automatic 500-600 character summaries using Google Gemini Flash

- **Asynchronous Processing**:
  - Redis Streams-based queue
  - Up to 5 concurrent document processing tasks
  - Support for up to 50 files per upload

- **Smart Caching**:
  - SHA256 hash-based document identification
  - Reuses existing results for duplicate PDFs

- **History**:
  - View last 10 processed documents with summaries

- **Document Validation**:
  - PDF-only uploads
  - 25MB size limit per file
  - Protected PDF detection

## Technology Stack

### Backend
- Python 3.14
- FastAPI 0.121.2
- Redis 8+ (Redis Streams)
- PyPDF 6.3.*
- Google Gemini Flash 2.5 (google-genai 0.3.*)
- Mistral OCR (mistralai 1.9.*)

### Frontend
- Next.js 14
- React 18
- TypeScript
- Server-Side Events (SSE) for real-time updates

### Infrastructure
- Docker & Docker Compose


## Quick Start

### 1. Clone the Repository

```bash
cd pdf_parser
```

### 2. Set Up Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
```env
GEMINI_API_KEY=your_gemini_api_key_here
MISTRAL_API_KEY=your_mistral_api_key_here
```

### 3. Run with Docker Compose

```bash
docker-compose up --build

# clean:
# docker-compose down --rmi=all --volumes
```

This will start:
- Redis (port 6379)
- Backend API (port 8000)
- Background Processor
- Frontend (port 3000)

### 4. Access the Application
- **Frontend**: http://localhost:3000

## Local Development

### Backend

```bash
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements-dev.txt

# Run Redis (required)
docker run -d -p 6379:6379 redis:8-alpine

# Run backend
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run processor (in separate terminal)
cd backend
python -m app.processor
```

### Running Tests

```bash
# Backend tests
cd backend
pytest -sv
```

## API Endpoints

### POST /upload
Upload PDF files for processing

**Request**:
- `files`: List of PDF files (multipart/form-data)
- `parser_type`: "gemini" | "mistral" | "pypdf" (form field)

**Response**:
```json
[
  {
    "success": true,
    "message": "File test.pdf added to queue",
    "pdf_hash": "abc123...",
    "queue_position": 3
  }
]
```

### GET /document/{pdf_hash}
Get processed document by hash

**Response**:
```json
{
  "pdf_hash": "abc123...",
  "extracted_text": "# Document Title\n\nContent...",
  "summary": "This document discusses...",
  "original_filename": "test.pdf",
  "parser_type": "gemini"
}
```

### GET /status/{pdf_hash}
Check processing status

**Response**:
```json
{
  "pdf_hash": "abc123...",
  "status": "completed",
  "message": "Document processed successfully"
}
```

### GET /history
Get last 10 processed documents

**Response**:
```json
{
  "documents": [...]
}
```

### GET /health
Health check

**Response**:
```json
{
  "status": "healthy",
  "redis": "connected"
}
```

## Architecture

### Processing Flow

1. User uploads PDF(s) via web interface
2. Backend validates files and calculates SHA256 hash
3. Checks if document already processed (cache hit)
4. If new, adds to Redis Streams queue
5. Background processor picks up tasks (max 5 concurrent)
6. Parses PDF using selected method
7. Generates summary using Gemini
8. Stores results in Redis
9. Frontend polls for updates and displays results

### Redis Data Structure

- **Stream**: `pdf_processing_queue` - Task queue
- **Hash**: `doc:{pdf_hash}` - Processed documents
- **List**: `doc:history` - Last 10 document hashes
- **String**: `pdf:raw:{pdf_hash}` - Raw PDF data (1 hour TTL)
