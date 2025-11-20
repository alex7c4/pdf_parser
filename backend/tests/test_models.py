"""Tests for Pydantic models"""
import pytest
from pydantic import ValidationError

from app.models import DocumentResponse, DocumentStatus, UploadResponse, HistoryResponse, ErrorResponse


class TestUploadResponse:
    """Test UploadResponse model"""

    def test_valid_upload_response(self) -> None:
        """Test creating valid upload response"""
        response = UploadResponse(success=True, message="Success", pdf_hash="abc123", queue_position=1)

        assert response.success is True
        assert response.message == "Success"
        assert response.pdf_hash == "abc123"
        assert response.queue_position == 1

    def test_upload_response_optional_fields(self) -> None:
        """Test upload response with optional fields"""
        response = UploadResponse(success=False, message="Error")

        assert response.success is False
        assert response.message == "Error"
        assert response.pdf_hash is None
        assert response.queue_position is None


class TestDocumentResponse:
    """Test DocumentResponse model"""

    def test_valid_document_response(self) -> None:
        """Test creating valid document response"""
        response = DocumentResponse(
            pdf_hash="abc123",
            extracted_text="Some text",
            summary="Summary",
            original_filename="test.pdf",
            parser_type="gemini",
        )

        assert response.pdf_hash == "abc123"
        assert response.extracted_text == "Some text"
        assert response.summary == "Summary"
        assert response.original_filename == "test.pdf"
        assert response.parser_type == "gemini"


class TestDocumentStatus:
    """Test DocumentStatus model"""

    def test_valid_status(self) -> None:
        """Test creating valid status"""
        status = DocumentStatus(pdf_hash="abc123", status="completed", message="Done")

        assert status.pdf_hash == "abc123"
        assert status.status == "completed"
        assert status.message == "Done"

    def test_invalid_status(self) -> None:
        """Test invalid status value"""
        with pytest.raises(ValidationError):
            DocumentStatus(pdf_hash="abc123", status="invalid_status", message="Test")


class TestHistoryResponse:
    """Test HistoryResponse model"""

    def test_empty_history(self) -> None:
        """Test creating empty history"""
        history = HistoryResponse(documents=[])

        assert len(history.documents) == 0

    def test_history_with_documents(self) -> None:
        """Test history with documents"""
        doc = DocumentResponse(
            pdf_hash="abc123",
            extracted_text="Text",
            summary="Summary",
            original_filename="test.pdf",
            parser_type="gemini",
        )
        history = HistoryResponse(documents=[doc])

        assert len(history.documents) == 1
        assert history.documents[0].pdf_hash == "abc123"


class TestErrorResponse:
    """Test ErrorResponse model"""

    def test_error_response(self) -> None:
        """Test creating error response"""
        error = ErrorResponse(error="Something went wrong", detail="More details")

        assert error.error == "Something went wrong"
        assert error.detail == "More details"
