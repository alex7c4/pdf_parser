"""Tests for Redis client"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.redis_client import RedisClient


class TestRedisClient:
    """Test Redis client functionality"""

    @pytest.mark.asyncio
    async def test_connect(self) -> None:
        """Test Redis connection"""
        with patch("app.redis_client.redis.Redis") as mock_redis:
            mock_instance = AsyncMock()
            # Mock Redis as a coroutine that returns the mock instance
            async def mock_redis_init(*args, **kwargs):
                return mock_instance
            mock_redis.side_effect = mock_redis_init
            mock_instance.xgroup_create = AsyncMock()

            client = RedisClient("localhost", 6379, 0)
            await client.connect()

            assert client.client is not None
            mock_instance.xgroup_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect(self) -> None:
        """Test Redis disconnection"""
        client = RedisClient("localhost", 6379, 0)
        client.client = AsyncMock()

        await client.disconnect()
        client.client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_to_queue(self) -> None:
        """Test adding document to queue"""
        client = RedisClient("localhost", 6379, 0)
        client.client = AsyncMock()
        client.client.xadd = AsyncMock(return_value=b"msg-123")
        client.client.set = AsyncMock()

        pdf_data = b"fake pdf"
        message_id = await client.add_to_queue("hash123", pdf_data, "gemini", "hash123:gemini", "test.pdf")

        assert message_id == "msg-123"
        client.client.xadd.assert_called_once()
        client.client.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_document(self) -> None:
        """Test saving document"""
        client = RedisClient("localhost", 6379, 0)
        client.client = AsyncMock()
        client.client.hset = AsyncMock()
        client.client.lpush = AsyncMock()
        client.client.ltrim = AsyncMock()

        await client.save_document("hash123", "extracted text", "summary", "test.pdf", "gemini")

        client.client.hset.assert_called_once()
        client.client.lpush.assert_called_once()
        client.client.ltrim.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_document(self) -> None:
        """Test retrieving document"""
        client = RedisClient("localhost", 6379, 0)
        client.client = AsyncMock()
        client.client.hgetall = AsyncMock(
            return_value={"pdf_hash": "hash123", "extracted_text": "text", "summary": "summary"}
        )

        doc = await client.get_document("hash123")

        assert doc is not None
        assert doc["pdf_hash"] == "hash123"
        client.client.hgetall.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_history(self) -> None:
        """Test retrieving history"""
        client = RedisClient("localhost", 6379, 0)
        client.client = AsyncMock()
        client.client.lrange = AsyncMock(return_value=["hash1", "hash2"])
        client.client.hgetall = AsyncMock(
            side_effect=[
                {"pdf_hash": "hash1", "summary": "summary1"},
                {"pdf_hash": "hash2", "summary": "summary2"},
            ]
        )

        history = await client.get_history(10)

        assert len(history) == 2
        assert history[0]["pdf_hash"] == "hash1"
        assert history[1]["pdf_hash"] == "hash2"
