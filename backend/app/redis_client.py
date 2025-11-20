"""Redis client and connection management"""
import json
from typing import Any, Dict, List, Optional

import redis.asyncio as redis

from app.config import constants


class RedisClient:
    """Redis client wrapper for document storage and queue management"""

    def __init__(self, host: str, port: int, db: int) -> None:
        self.host = host
        self.port = port
        self.db = db
        self.client: Optional[redis.Redis] = None
        self.stream_name = constants.REDIS_STREAM_NAME
        self.consumer_group = constants.REDIS_CONSUMER_GROUP
        self.consumer_name = constants.REDIS_CONSUMER_NAME

    async def connect(self) -> None:
        """Establish Redis connection"""
        self.client = await redis.Redis(host=self.host, port=self.port, db=self.db, decode_responses=False)
        # Create consumer group if not exists
        try:
            await self.client.xgroup_create(self.stream_name, self.consumer_group, id=b"0", mkstream=True)
        except redis.ResponseError:
            pass  # Group already exists

    async def disconnect(self) -> None:
        """Close Redis connection"""
        if self.client:
            await self.client.close()

    async def add_to_queue(self, pdf_hash: str, file_data: bytes, parser_type: str, doc_key: str, filename: str = None) -> str:
        """Add document to processing queue using Redis Streams"""
        if not self.client:
            raise RuntimeError(constants.MSG_REDIS_CLIENT_NOT_CONNECTED)

        message_data = {
            b"pdf_hash": pdf_hash.encode(),
            b"parser_type": parser_type.encode(),
            b"doc_key": doc_key.encode(),
            b"status": constants.STATUS_PENDING.encode()
        }

        if filename:
            message_data[b"filename"] = filename.encode()

        message_id = await self.client.xadd(self.stream_name, message_data)
        # Store file data separately
        raw_key = f"{constants.REDIS_PDF_RAW_KEY_PREFIX}{pdf_hash}"
        await self.client.set(raw_key, file_data, ex=constants.RAW_PDF_TTL_SECONDS)
        return message_id.decode()

    async def get_from_queue(self, count: int = 1, block: int = None) -> List[Dict[str, Any]]:
        """Retrieve messages from queue"""
        if not self.client:
            raise RuntimeError(constants.MSG_REDIS_CLIENT_NOT_CONNECTED)

        block_time = block if block is not None else constants.QUEUE_BLOCK_TIME_MS
        messages = await self.client.xreadgroup(
            self.consumer_group, self.consumer_name, {self.stream_name: b">"}, count=count, block=block_time
        )

        result = []
        for stream_name, stream_messages in messages:
            for message_id, data in stream_messages:
                # Decode bytes to strings
                decoded_data = {k.decode() if isinstance(k, bytes) else k: v.decode() if isinstance(v, bytes) else v for k, v in data.items()}
                result.append({"id": message_id.decode() if isinstance(message_id, bytes) else message_id, "data": decoded_data})
        return result

    async def acknowledge_message(self, message_id: str) -> None:
        """Acknowledge processed message"""
        if not self.client:
            raise RuntimeError(constants.MSG_REDIS_CLIENT_NOT_CONNECTED)
        await self.client.xack(self.stream_name, self.consumer_group, message_id)

    async def save_document(
        self, doc_key: str, extracted_text: str, summary: str, original_filename: str, parser_type: str, status: str = None, error: str = None
    ) -> None:
        """Save processed document to Redis"""
        if not self.client:
            raise RuntimeError(constants.MSG_REDIS_CLIENT_NOT_CONNECTED)

        doc_data = {
            b"doc_key": doc_key.encode(),
            b"extracted_text": extracted_text.encode(),
            b"summary": summary.encode(),
            b"original_filename": original_filename.encode(),
            b"parser_type": parser_type.encode(),
            b"status": (status or constants.STATUS_COMPLETED).encode(),
        }

        if error:
            doc_data[b"error"] = error.encode()

        redis_key = f"{constants.REDIS_DOC_KEY_PREFIX}{doc_key}"
        await self.client.hset(redis_key, mapping=doc_data)
        # Add to history list
        await self.client.lpush(constants.REDIS_HISTORY_KEY, doc_key.encode())
        await self.client.ltrim(constants.REDIS_HISTORY_KEY, 0, constants.HISTORY_LIMIT - 1)

    async def get_document(self, doc_key: str) -> Optional[Dict[str, str]]:
        """Retrieve document by composite key"""
        if not self.client:
            raise RuntimeError(constants.MSG_REDIS_CLIENT_NOT_CONNECTED)

        redis_key = f"{constants.REDIS_DOC_KEY_PREFIX}{doc_key}"
        doc_data = await self.client.hgetall(redis_key)
        if doc_data:
            # Decode bytes to strings
            return {k.decode() if isinstance(k, bytes) else k: v.decode() if isinstance(v, bytes) else v for k, v in doc_data.items()}
        return None

    async def get_history(self, limit: int = None) -> List[Dict[str, str]]:
        """Get last N processed documents"""
        if not self.client:
            raise RuntimeError(constants.MSG_REDIS_CLIENT_NOT_CONNECTED)

        history_limit = limit if limit is not None else constants.HISTORY_LIMIT
        doc_keys = await self.client.lrange(constants.REDIS_HISTORY_KEY, 0, history_limit - 1)
        documents = []

        for doc_key in doc_keys:
            # Decode key if it's bytes
            doc_key_str = doc_key.decode() if isinstance(doc_key, bytes) else doc_key
            doc = await self.get_document(doc_key_str)
            if doc:
                documents.append(doc)

        return documents

    async def get_raw_pdf(self, pdf_hash: str) -> Optional[bytes]:
        """Get raw PDF data"""
        if not self.client:
            raise RuntimeError(constants.MSG_REDIS_CLIENT_NOT_CONNECTED)

        raw_key = f"{constants.REDIS_PDF_RAW_KEY_PREFIX}{pdf_hash}"
        data = await self.client.get(raw_key)
        # Data is already bytes since decode_responses=False
        return data if data else None

    async def get_queue_length(self) -> int:
        """Get number of pending items in queue"""
        if not self.client:
            raise RuntimeError(constants.MSG_REDIS_CLIENT_NOT_CONNECTED)

        info = await self.client.xinfo_stream(self.stream_name)
        return info.get("length", 0)
