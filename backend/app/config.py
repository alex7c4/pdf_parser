"""Application configuration"""
import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Get the project root directory (3 levels up from this file)
PROJECT_ROOT = Path(__file__).parent.parent.parent
ENV_FILE_PATH = PROJECT_ROOT / ".env"

# Load .env file explicitly
if ENV_FILE_PATH.exists():
    load_dotenv(ENV_FILE_PATH)


class AppConstants:
    """Application constants that don't change"""

    # API information
    API_TITLE: str = "PDF Parser API"
    API_VERSION: str = "0.1.0"

    # Model names
    GEMINI_MODEL: str = "gemini-2.5-flash"
    MISTRAL_MODEL: str = "mistral-small-latest"

    # Parser types
    PARSER_TYPE_PYPDF: str = "pypdf"
    PARSER_TYPE_GEMINI: str = "gemini"
    PARSER_TYPE_MISTRAL: str = "mistral"
    DEFAULT_PARSER_TYPE: str = PARSER_TYPE_GEMINI

    # Redis keys and names
    REDIS_STREAM_NAME: str = "pdf_processing_queue"
    REDIS_CONSUMER_GROUP: str = "pdf_processors"
    REDIS_CONSUMER_NAME: str = "processor_1"
    REDIS_DOC_KEY_PREFIX: str = "doc:"
    REDIS_PDF_RAW_KEY_PREFIX: str = "pdf:raw:"
    REDIS_HISTORY_KEY: str = "doc:history"

    # Redis TTL
    RAW_PDF_TTL_SECONDS: int = 3600  # 1 hour

    # File validation
    PDF_FILE_EXTENSION: str = ".pdf"
    FILE_SIZE_DISPLAY_MB: int = 25
    PDF_MIME_TYPE: str = "application/pdf"

    # Processing limits
    HISTORY_LIMIT: int = 10
    SUMMARY_MIN_LENGTH: int = 500
    SUMMARY_MAX_LENGTH_TARGET: int = 600
    TEXT_INPUT_LIMIT_CHARS: int = 50_000  # Max chars to send to summarizer

    # Timeouts (milliseconds/seconds)
    GEMINI_PARSE_TIMEOUT_SECONDS: int = 60
    GEMINI_SUMMARY_TIMEOUT_SECONDS: int = 30
    QUEUE_BLOCK_TIME_MS: int = 5000
    PROCESSOR_SLEEP_SECONDS: int = 1
    PROCESSOR_ERROR_SLEEP_SECONDS: int = 5

    # Logging
    LOG_LEVEL: str = "INFO"

    # HTTP Status messages
    MSG_REDIS_CONNECTED: str = "Redis connected"
    MSG_REDIS_DISCONNECTED: str = "Redis disconnected"
    MSG_REDIS_CLIENT_NOT_CONNECTED: str = "Redis client not connected"
    MSG_PROCESSING_STARTED: str = "Starting document processor"
    MSG_DOCUMENT_NOT_FOUND: str = "Document not found"
    MSG_DOCUMENT_PROCESSED: str = "Document processed successfully"
    MSG_FILE_NOT_PDF: str = "is not a PDF"
    MSG_FILE_TOO_LARGE: str = "exceeds maximum size of 25MB"
    MSG_ALREADY_PROCESSED: str = "already processed (using cached result)"
    MSG_ADDED_TO_QUEUE: str = "added to queue"
    MSG_IN_QUEUE: str = "Document in queue (position: ~)"

    # Status values
    STATUS_PENDING: str = "pending"
    STATUS_COMPLETED: str = "completed"
    STATUS_ERROR: str = "error"
    STATUS_HEALTHY: str = "healthy"
    STATUS_UNHEALTHY: str = "unhealthy"

    # CORS
    CORS_ALLOW_ORIGINS: list = ["*"]  # In production, specify exact origins
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list = ["*"]
    CORS_ALLOW_HEADERS: list = ["*"]

    # Error messages
    ERROR_PDF_ENCRYPTED: str = "PDF is encrypted/protected"
    ERROR_PYPDF_PARSE: str = "Failed to parse PDF with PyPDF"
    ERROR_GEMINI_PARSE: str = "Failed to parse PDF with Gemini"
    ERROR_MISTRAL_PARSE: str = "Failed to parse PDF with Mistral"
    ERROR_SUMMARY_GENERATION: str = "Failed to generate summary"
    ERROR_UNKNOWN_PARSER: str = "Unknown parser type"
    ERROR_PDF_NOT_FOUND: str = "PDF data not found for"
    ERROR_ALREADY_PROCESSED: str = "already processed, skipping"
    ERROR_PROCESSING: str = "Error processing document"
    ERROR_PROCESSING_LOOP: str = "Error in processing loop"
    ERROR_PROCESSING_FILE: str = "Error processing file"

    # Prompts
    GEMINI_EXTRACTION_PROMPT: str = (
        """Extract all text, tables, and content from this PDF document.
        Format the output as Markdown. 
        Include:
        - All text content
        - Tables in markdown table format
        - Any text from images or graphics
        - Preserve document structure with appropriate headers
        Return only the Markdown content without any additional commentary.
    """).strip()

    MISTRAL_EXTRACTION_PROMPT: str = GEMINI_EXTRACTION_PROMPT

    SUMMARY_PROMPT_TEMPLATE: str = (
        """Summarize the following document in approximately 500-600 characters.
        Focus on the main points and key information.
        Format the summary as clean markdown.

        Document text:
        {text}
    """).strip()


class Settings(BaseSettings):
    """Application settings from environment variables"""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    # API Keys (loaded from environment variables)
    gemini_api_key: str = ""
    mistral_api_key: str = ""

    # Application
    max_file_size: int = 25*1024*1024  # 25MB
    max_files_per_upload: int = 50
    max_concurrent_processing: int = 5
    summary_max_length: int = 600

    # Server
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000


# Singleton instances
constants = AppConstants()
settings = Settings()
