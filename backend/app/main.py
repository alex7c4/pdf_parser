"""FastAPI application"""
import hashlib
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, List, Literal

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import constants, settings
from app.models import DocumentResponse, DocumentStatus, ErrorResponse, HistoryResponse, UploadResponse
from app.redis_client import RedisClient

logging.basicConfig(level=constants.LOG_LEVEL)
logger = logging.getLogger(__name__)

# Global Redis client
redis_client: RedisClient = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Lifespan context manager"""
    global redis_client
    redis_client = RedisClient(settings.redis_host, settings.redis_port, settings.redis_db)
    await redis_client.connect()
    logger.info(constants.MSG_REDIS_CONNECTED)
    yield
    await redis_client.disconnect()
    logger.info(constants.MSG_REDIS_DISCONNECTED)


app = FastAPI(title=constants.API_TITLE, version=constants.API_VERSION, lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=constants.CORS_ALLOW_ORIGINS,
    allow_credentials=constants.CORS_ALLOW_CREDENTIALS,
    allow_methods=constants.CORS_ALLOW_METHODS,
    allow_headers=constants.CORS_ALLOW_HEADERS,
)


def calculate_pdf_hash(data: bytes) -> str:
    """Calculate SHA256 hash of PDF data"""
    return hashlib.sha256(data).hexdigest()


def get_document_key(pdf_hash: str, parser_type: str) -> str:
    """Generate composite key for document storage"""
    return f"{pdf_hash}:{parser_type}"


@app.get("/")
async def root() -> dict:
    """Root endpoint"""
    return {"message": constants.API_TITLE, "version": constants.API_VERSION}


@app.post("/upload", response_model=List[UploadResponse])
async def upload_pdfs(
    files: List[UploadFile] = File(...),
    parser_type: Literal["pypdf", "gemini", "mistral"] = Form(default=None),
) -> List[UploadResponse]:
    """Upload one or more PDF files for processing"""
    # Use default parser type if not specified
    selected_parser_type = parser_type if parser_type is not None else constants.DEFAULT_PARSER_TYPE

    if len(files) > settings.max_files_per_upload:
        raise HTTPException(
            status_code=400, detail=f"Too many files. Maximum {settings.max_files_per_upload} files allowed"
        )

    responses = []

    for file in files:
        try:
            # Validate file type
            if not file.filename.lower().endswith(constants.PDF_FILE_EXTENSION):
                responses.append(
                    UploadResponse(
                        success=False, message=f"File {file.filename} {constants.MSG_FILE_NOT_PDF}", pdf_hash=None
                    )
                )
                continue

            # Read file content
            content = await file.read()

            # Validate file size
            if len(content) > settings.max_file_size:
                responses.append(
                    UploadResponse(success=False, message=f"File {file.filename} {constants.MSG_FILE_TOO_LARGE}", pdf_hash=None)
                )
                continue

            # Calculate hash
            pdf_hash = calculate_pdf_hash(content)
            doc_key = get_document_key(pdf_hash, selected_parser_type)

            # Check if already processed with this parser
            existing_doc = await redis_client.get_document(doc_key)
            if existing_doc:
                # Only use cached result if previous processing was successful
                status = existing_doc.get("status", constants.STATUS_COMPLETED)
                if status != constants.STATUS_ERROR:
                    responses.append(
                        UploadResponse(
                            success=True,
                            message=f"File {file.filename} {constants.MSG_ALREADY_PROCESSED}",
                            pdf_hash=doc_key,
                            queue_position=0,
                        )
                    )
                    continue
                # If previous processing had errors, reprocess by continuing to queue addition

            # Add to queue
            await redis_client.add_to_queue(pdf_hash, content, selected_parser_type, doc_key, file.filename)
            queue_length = await redis_client.get_queue_length()

            responses.append(
                UploadResponse(
                    success=True,
                    message=f"File {file.filename} {constants.MSG_ADDED_TO_QUEUE}",
                    pdf_hash=doc_key,
                    queue_position=queue_length,
                )
            )

        except Exception as e:
            logger.error(f"{constants.ERROR_PROCESSING_FILE} {file.filename}: {str(e)}")
            responses.append(
                UploadResponse(success=False, message=f"Error processing {file.filename}: {str(e)}", pdf_hash=None)
            )

    return responses


@app.get("/document/{doc_key:path}", response_model=DocumentResponse)
async def get_document(doc_key: str) -> DocumentResponse:
    """Get processed document by composite key"""
    doc = await redis_client.get_document(doc_key)

    if not doc:
        raise HTTPException(status_code=404, detail=constants.MSG_DOCUMENT_NOT_FOUND)

    return DocumentResponse(
        pdf_hash=doc.get("doc_key", doc_key),
        extracted_text=doc.get("extracted_text", ""),
        summary=doc.get("summary", ""),
        original_filename=doc.get("original_filename", ""),
        parser_type=doc.get("parser_type", ""),
        status=doc.get("status", constants.STATUS_COMPLETED),
        error=doc.get("error"),
    )


@app.get("/status/{doc_key:path}", response_model=DocumentStatus)
async def get_status(doc_key: str) -> DocumentStatus:
    """Get processing status of a document"""
    # Check if completed or error
    doc = await redis_client.get_document(doc_key)
    if doc:
        status = doc.get("status", constants.STATUS_COMPLETED)
        error = doc.get("error")

        if status == constants.STATUS_ERROR:
            return DocumentStatus(
                pdf_hash=doc_key,
                status=constants.STATUS_ERROR,
                message="Processing failed",
                error=error
            )

        return DocumentStatus(
            pdf_hash=doc_key,
            status=status,
            message=constants.MSG_DOCUMENT_PROCESSED
        )

    # Check if in queue
    queue_length = await redis_client.get_queue_length()
    if queue_length > 0:
        return DocumentStatus(pdf_hash=doc_key, status=constants.STATUS_PENDING, message=constants.MSG_IN_QUEUE)

    return DocumentStatus(pdf_hash=doc_key, status=constants.STATUS_ERROR, message=constants.MSG_DOCUMENT_NOT_FOUND)


@app.get("/history", response_model=HistoryResponse)
async def get_history() -> HistoryResponse:
    """Get last 10 processed documents"""
    docs = await redis_client.get_history(limit=constants.HISTORY_LIMIT)

    documents = [
        DocumentResponse(
            pdf_hash=doc.get("doc_key", ""),
            extracted_text=doc.get("extracted_text", ""),
            summary=doc.get("summary", ""),
            original_filename=doc.get("original_filename", ""),
            parser_type=doc.get("parser_type", ""),
            status=doc.get("status", constants.STATUS_COMPLETED),
            error=doc.get("error"),
        )
        for doc in docs
    ]

    return HistoryResponse(documents=documents)


@app.get("/health")
async def health() -> dict:
    """Health check endpoint"""
    try:
        # Check Redis connection
        if redis_client and redis_client.client:
            await redis_client.client.ping()
            return {"status": constants.STATUS_HEALTHY, "redis": "connected"}
        else:
            return {"status": constants.STATUS_UNHEALTHY, "redis": "disconnected"}
    except Exception as e:
        return {"status": constants.STATUS_UNHEALTHY, "error": str(e)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.backend_host, port=settings.backend_port)
