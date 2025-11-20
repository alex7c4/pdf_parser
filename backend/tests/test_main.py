"""Tests for FastAPI application"""
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app, calculate_pdf_hash


class TestCalculatePdfHash:
    """Test PDF hash calculation"""

    def test_hash_calculation(self) -> None:
        """Test hash calculation produces consistent results"""
        data = b"test data"
        hash1 = calculate_pdf_hash(data)
        hash2 = calculate_pdf_hash(data)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 produces 64 hex characters

    def test_different_data_different_hash(self) -> None:
        """Test different data produces different hashes"""
        hash1 = calculate_pdf_hash(b"data1")
        hash2 = calculate_pdf_hash(b"data2")

        assert hash1 != hash2


class TestHealthEndpoint:
    """Test health check endpoint"""

    def test_health_endpoint_structure(self) -> None:
        """Test health endpoint returns expected structure"""
        client = TestClient(app)
        # Note: This will fail without Redis, but tests the endpoint structure
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data


class TestRootEndpoint:
    """Test root endpoint"""

    def test_root_endpoint(self) -> None:
        """Test root endpoint returns expected data"""
        client = TestClient(app)
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "PDF Parser API"
        assert "version" in data
