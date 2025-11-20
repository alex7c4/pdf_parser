"""Background processor for PDF documents"""
import asyncio
import hashlib
import logging
from typing import Optional

from app.config import constants, settings
from app.parsers import SummarizerService, get_parser
from app.redis_client import RedisClient

logging.basicConfig(level=constants.LOG_LEVEL)
logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Processes PDF documents from Redis queue"""

    def __init__(self, redis_client: RedisClient) -> None:
        self.redis_client = redis_client
        self.summarizer = SummarizerService(settings.gemini_api_key, settings.summary_max_length)
        self.max_concurrent = settings.max_concurrent_processing
        self.processing_semaphore = asyncio.Semaphore(self.max_concurrent)

    async def process_document(self, message_id: str, pdf_hash: str, parser_type: str, doc_key: str, filename: str = None) -> None:
        """Process a single document"""
        async with self.processing_semaphore:
            try:
                logger.info(f"Processing document '{filename}' {doc_key} with '{parser_type}'")

                # Check if already processed successfully
                existing_doc = await self.redis_client.get_document(doc_key)
                if existing_doc:
                    status = existing_doc.get("status", constants.STATUS_COMPLETED)
                    # Only skip if previous processing was successful
                    if status != constants.STATUS_ERROR:
                        logger.info(f"Document '{filename}' {doc_key} {constants.ERROR_ALREADY_PROCESSED}")
                        await self.redis_client.acknowledge_message(message_id)
                        return
                    # If previous processing had errors, continue to reprocess
                    logger.info(f"Reprocessing document '{filename}' {doc_key} (previous attempt failed)")

                # Get raw PDF data
                pdf_data = await self.redis_client.get_raw_pdf(pdf_hash)
                if not pdf_data:
                    logger.error(f"{constants.ERROR_PDF_NOT_FOUND} {pdf_hash}")
                    await self.redis_client.acknowledge_message(message_id)
                    return

                # Parse PDF
                parser = get_parser(parser_type, settings.gemini_api_key, settings.mistral_api_key)
                extracted_text = await parser.parse(pdf_data)

                # Generate summary
                summary = await self.summarizer.generate_summary(extracted_text)

                # Save to Redis
                await self.redis_client.save_document(
                    doc_key=doc_key,
                    extracted_text=extracted_text,
                    summary=summary,
                    original_filename=filename or doc_key,
                    parser_type=parser_type,
                )

                # Acknowledge message
                await self.redis_client.acknowledge_message(message_id)
                logger.info(f"Successfully processed document '{filename}' {doc_key}")

            except Exception as e:
                error_msg = str(e)
                logger.error(f"{constants.ERROR_PROCESSING} '{filename}' {doc_key}: {error_msg}")

                # Save error state to Redis so frontend can display it
                await self.redis_client.save_document(
                    doc_key=doc_key,
                    extracted_text="",
                    summary="",
                    original_filename=filename or doc_key,
                    parser_type=parser_type,
                    status=constants.STATUS_ERROR,
                    error=error_msg,
                )

                # Acknowledge message to prevent infinite retries
                await self.redis_client.acknowledge_message(message_id)

    async def run(self) -> None:
        """Main processing loop"""
        logger.info(constants.MSG_PROCESSING_STARTED)
        await self.redis_client.connect()

        try:
            while True:
                try:
                    # Get messages from queue
                    messages = await self.redis_client.get_from_queue(count=self.max_concurrent)

                    if messages:
                        # Process messages concurrently
                        tasks = []
                        for msg in messages:
                            pdf_hash = msg["data"].get("pdf_hash")
                            parser_type = msg["data"].get("parser_type", constants.DEFAULT_PARSER_TYPE)
                            doc_key = msg["data"].get("doc_key")
                            filename = msg["data"].get("filename")
                            message_id = msg["id"]

                            if pdf_hash and doc_key:
                                task = asyncio.create_task(
                                    self.process_document(message_id, pdf_hash, parser_type, doc_key, filename)
                                )
                                tasks.append(task)

                        await asyncio.gather(*tasks, return_exceptions=True)
                    else:
                        # No messages, wait a bit
                        await asyncio.sleep(constants.PROCESSOR_SLEEP_SECONDS)

                except Exception as e:
                    logger.error(f"{constants.ERROR_PROCESSING_LOOP}: {str(e)}")
                    await asyncio.sleep(constants.PROCESSOR_ERROR_SLEEP_SECONDS)

        finally:
            await self.redis_client.disconnect()


async def start_processor() -> None:
    """Start the background processor"""
    redis_client = RedisClient(settings.redis_host, settings.redis_port, settings.redis_db)
    processor = DocumentProcessor(redis_client)
    await processor.run()


if __name__ == "__main__":
    asyncio.run(start_processor())
