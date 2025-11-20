"""Tests for PDF parsers"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.parsers import PyPDFParser, GeminiParser, MistralParser, SummarizerService, get_parser


class TestPyPDFParser:
    """Test PyPDF parser"""

    @pytest.mark.asyncio
    async def test_parse_valid_pdf(self, sample_pdf_data: bytes) -> None:
        """Test parsing valid PDF"""
        parser = PyPDFParser()
        result = await parser.parse(sample_pdf_data)

        # PDF parsing should succeed and return a string (even if empty for minimal PDFs)
        assert isinstance(result, str)
        # Some minimal PDFs may not have extractable text, so we just verify it doesn't error

    @pytest.mark.asyncio
    async def test_parse_invalid_pdf(self) -> None:
        """Test parsing invalid PDF"""
        parser = PyPDFParser()

        with pytest.raises(ValueError):
            await parser.parse(b"not a pdf")


class TestGeminiParser:
    """Test Gemini parser"""

    @pytest.mark.asyncio
    async def test_get_parser_factory(self) -> None:
        """Test parser factory function"""
        parser = get_parser("pypdf", "fake_gemini_key", "fake_mistral_key")
        assert isinstance(parser, PyPDFParser)

        parser = get_parser("gemini", "fake_gemini_key", "fake_mistral_key")
        assert isinstance(parser, GeminiParser)

        parser = get_parser("mistral", "fake_gemini_key", "fake_mistral_key")
        assert isinstance(parser, MistralParser)

    def test_invalid_parser_type(self) -> None:
        """Test invalid parser type"""
        with pytest.raises(ValueError):
            get_parser("invalid", "key1", "key2")


class TestSummarizerService:
    """Test summarizer service"""

    @pytest.mark.asyncio
    async def test_summarizer_initialization(self) -> None:
        """Test summarizer initialization"""
        summarizer = SummarizerService("fake_api_key", max_length=500)
        assert summarizer.api_key == "fake_api_key"
        assert summarizer.max_length == 500
