"""PDF parsing services"""
import base64
from abc import ABC, abstractmethod
from typing import Optional

from google import genai
from google.genai import types
from mistralai import Mistral
from pypdf import PdfReader

from app.config import constants


class PDFParser(ABC):
    """Abstract base class for PDF parsers"""

    @abstractmethod
    async def parse(self, pdf_data: bytes) -> str:
        """Parse PDF and return extracted text/markdown"""
        pass


class PyPDFParser(PDFParser):
    """PyPDF-based parser (plain text only)"""

    async def parse(self, pdf_data: bytes) -> str:
        """Extract plain text from PDF"""
        try:
            import io

            pdf_file = io.BytesIO(pdf_data)
            reader = PdfReader(pdf_file)

            if reader.is_encrypted:
                raise ValueError(constants.ERROR_PDF_ENCRYPTED)

            text_parts = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)

            return "\n\n".join(text_parts)
        except Exception as e:
            raise ValueError(f"{constants.ERROR_PYPDF_PARSE}: {str(e)}")


class GeminiParser(PDFParser):
    """Google Gemini Flash 2.5 parser (markdown output)"""

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self.client = genai.Client(api_key=api_key)

    async def parse(self, pdf_data: bytes) -> str:
        """Extract markdown from PDF using Gemini Vision"""
        try:
            # Use the new google-genai API with proper Part types
            response = self.client.models.generate_content(
                model=constants.GEMINI_MODEL,
                contents=[
                    types.Part.from_bytes(data=pdf_data, mime_type=constants.PDF_MIME_TYPE),
                    constants.GEMINI_EXTRACTION_PROMPT,
                ]
            )
            return response.text
        except Exception as e:
            raise ValueError(f"{constants.ERROR_GEMINI_PARSE}: {str(e)}")


class MistralParser(PDFParser):
    """Mistral OCR parser (markdown output)"""

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self.client = Mistral(api_key=api_key)

    async def parse(self, pdf_data: bytes) -> str:
        """Extract markdown from PDF using Mistral OCR"""
        try:
            # Convert PDF to base64
            pdf_base64 = base64.b64encode(pdf_data).decode("utf-8")

            # Mistral OCR uses document_url instead of image_url
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": constants.MISTRAL_EXTRACTION_PROMPT},
                        {"type": "document_url", "document_url": f"data:{constants.PDF_MIME_TYPE};base64,{pdf_base64}"},
                    ],
                }
            ]
            response = self.client.chat.complete(
                model=constants.MISTRAL_MODEL,
                messages=messages
            )
            return response.choices[0].message.content
        except Exception as e:
            raise ValueError(f"{constants.ERROR_MISTRAL_PARSE}: {str(e)}")


class SummarizerService:
    """PDF summary generation using Gemini"""

    def __init__(self, api_key: str, max_length: int = None) -> None:
        self.api_key = api_key
        self.max_length = max_length if max_length is not None else constants.SUMMARY_MAX_LENGTH_TARGET
        self.client = genai.Client(api_key=api_key)

    async def generate_summary(self, text: str) -> str:
        """Generate summary from extracted text"""
        try:
            # Limit input text to avoid token limits
            truncated_text = text[: constants.TEXT_INPUT_LIMIT_CHARS]
            prompt = constants.SUMMARY_PROMPT_TEMPLATE.format(text=truncated_text)

            response = self.client.models.generate_content(
                model=constants.GEMINI_MODEL,
                contents=prompt
            )

            summary = response.text
            # Ensure summary is within length limit
            if len(summary) > self.max_length:
                summary = summary[: self.max_length - 3] + "..."

            return summary
        except Exception as e:
            raise ValueError(f"{constants.ERROR_SUMMARY_GENERATION}: {str(e)}")


def get_parser(parser_type: str, gemini_key: str, mistral_key: str) -> PDFParser:
    """Factory function to get appropriate parser"""
    if parser_type == "pypdf":
        return PyPDFParser()
    elif parser_type == "gemini":
        return GeminiParser(gemini_key)
    elif parser_type == "mistral":
        return MistralParser(mistral_key)
    else:
        raise ValueError(f"Unknown parser type: {parser_type}")
