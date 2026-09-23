from typing import List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.repositories.document_repo import DocumentRepository
from backend.app.services.document_service import DocumentProcessor
from backend.app.core.config import settings

async def search_knowledge_base(
    query: str,
    organization_id: str,
    db: AsyncSession,
    top_k: int = settings.RETRIEVAL_TOP_K
) -> List[Dict[str, Any]]:
    """
    Tool 1: Searches knowledge base chunks for relevant context.
    Strictly filters by organization_id to ensure tenant isolation.
    """
    repo = DocumentRepository(db)
    query_vector = DocumentProcessor.generate_embedding(query)
    scored_chunks = await repo.search_chunks(
        organization_id=organization_id,
        query_embedding=query_vector,
        top_k=top_k,
        similarity_threshold=settings.SIMILARITY_THRESHOLD
    )

    results = []
    for chunk, score, filename in scored_chunks:
        results.append({
            "chunk_id": chunk.id,
            "document_id": chunk.document_id,
            "document_name": filename,
            "page_number": chunk.page_number,
            "relevance_score": round(score, 4),
            "content": chunk.content
        })
    return results

async def get_faq(query: str, organization_id: str, db: AsyncSession) -> List[Dict[str, Any]]:
    """
    Tool 8: Searches structured FAQ records for immediate answers.
    """
    repo = DocumentRepository(db)
    faqs = await repo.search_faqs(organization_id=organization_id, query=query)
    return [
        {
            "id": faq.id,
            "question": faq.question,
            "answer": faq.answer,
            "category": faq.category
        }
        for faq in faqs
    ]
