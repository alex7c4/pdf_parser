"""Pydantic models for API"""
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    """Response for file upload"""

    success: bool
    message: str
    pdf_hash: Optional[str] = None
    queue_position: Optional[int] = None


class DocumentResponse(BaseModel):
    """Response for document retrieval"""

    pdf_hash: str
    extracted_text: str
    summary: str
    original_filename: str
    parser_type: str
    status: Optional[str] = "completed"
    error: Optional[str] = None


class DocumentStatus(BaseModel):
    """Status of a document"""

    pdf_hash: str
    status: Literal["pending", "processing", "completed", "error"]
    message: Optional[str] = None
    error: Optional[str] = None


class HistoryResponse(BaseModel):
    """Response for history retrieval"""

    documents: List[DocumentResponse]


class ErrorResponse(BaseModel):
    """Error response"""

    error: str
    detail: Optional[str] = None
