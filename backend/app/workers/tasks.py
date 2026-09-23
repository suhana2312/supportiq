import asyncio
import logging
from backend.app.workers.celery_app import celery_app
from backend.app.db.database import AsyncSessionLocal
from backend.app.services.document_service import DocumentProcessor

logger = logging.getLogger("supportiq.tasks")

@celery_app.task(name="process_document_task", bind=True, max_retries=3)
def process_document_task(self, document_id: str):
    logger.info(f"Starting Celery background processing for document: {document_id}")
    try:
        async def run_process():
            async with AsyncSessionLocal() as session:
                processor = DocumentProcessor(session)
                await processor.process_document(document_id)
        
        asyncio.run(run_process())
        logger.info(f"Successfully processed document: {document_id}")
        return {"status": "SUCCESS", "document_id": document_id}
    except Exception as exc:
        logger.error(f"Error processing document {document_id}: {str(exc)}")
        raise self.retry(exc=exc, countdown=10)

@celery_app.task(name="send_notification_email_task")
def send_notification_email_task(recipient_email: str, subject: str, message: str):
    logger.info(f"[EMAIL DISPATCH] To: {recipient_email} | Subject: {subject} | Content: {message[:100]}...")
    return {"status": "SENT", "recipient": recipient_email}
