"""Pytest configuration and fixtures"""
import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_redis_client() -> AsyncMock:
    """Mock Redis client"""
    client = AsyncMock()
    client.connect = AsyncMock()
    client.disconnect = AsyncMock()
    client.add_to_queue = AsyncMock(return_value="test-message-id")
    client.get_from_queue = AsyncMock(return_value=[])
    client.save_document = AsyncMock()
    client.get_document = AsyncMock(return_value=None)
    client.get_history = AsyncMock(return_value=[])
    client.get_raw_pdf = AsyncMock(return_value=b"fake pdf data")
    client.get_queue_length = AsyncMock(return_value=0)
    return client


@pytest.fixture
def sample_pdf_data() -> bytes:
    """Sample PDF data for testing"""
    # Minimal valid PDF structure with proper xref table and resources
    return b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
/Resources <<
/Font <<
/F1 <<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
>>
>>
>>
endobj
4 0 obj
<<
/Length 55
>>
stream
BT
/F1 12 Tf
100 700 Td
(Hello World) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000351 00000 n
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
456
%%EOF"""


@pytest.fixture
def sample_document() -> dict:
    """Sample document data"""
    return {
        "pdf_hash": "abc123",
        "extracted_text": "This is a test document with some text.",
        "summary": "Test document summary",
        "original_filename": "test.pdf",
        "parser_type": "gemini",
    }
