import json
import math
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, delete
from backend.app.models.models import Document, DocumentChunk, FAQ
from backend.app.models.enums import DocumentStatus
from backend.app.repositories.base import BaseRepository

def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)

class DocumentRepository(BaseRepository[Document]):
    def __init__(self, db: AsyncSession):
        super().__init__(Document, db)

    async def get_with_chunks(self, document_id: str, organization_id: str) -> Optional[Document]:
        result = await self.db.execute(
            select(Document).where(
                Document.id == document_id,
                Document.organization_id == organization_id
            )
        )
        return result.scalar_one_or_none()

    async def save_chunks(self, chunks: List[DocumentChunk]) -> None:
        self.db.add_all(chunks)
        await self.db.commit()

    async def delete_chunks_for_document(self, document_id: str) -> None:
        await self.db.execute(
            delete(DocumentChunk).where(DocumentChunk.document_id == document_id)
        )
        await self.db.commit()

    async def search_chunks(
        self,
        organization_id: str,
        query_embedding: List[float],
        top_k: int = 5,
        similarity_threshold: float = 0.35
    ) -> List[Tuple[DocumentChunk, float, str]]:
        """
        Retrieves top-k chunks strictly belonging to organization_id.
        Computes cosine similarity between query_embedding and stored chunk embeddings.
        Returns tuples of (DocumentChunk, score, document_name).
        """
        # Fetch chunks belonging to organization with document join
        stmt = (
            select(DocumentChunk, Document.filename)
            .join(Document, Document.id == DocumentChunk.document_id)
            .where(
                DocumentChunk.organization_id == organization_id,
                Document.status == DocumentStatus.PROCESSED
            )
        )
        result = await self.db.execute(stmt)
        rows = result.all()

        scored_chunks: List[Tuple[DocumentChunk, float, str]] = []
        for chunk, filename in rows:
            if not chunk.embedding_json:
                continue
            try:
                emb = json.loads(chunk.embedding_json)
                score = cosine_similarity(query_embedding, emb)
                if score >= similarity_threshold:
                    scored_chunks.append((chunk, score, filename))
            except Exception:
                continue

        # Sort descending by score and pick top_k
        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        return scored_chunks[:top_k]

    # FAQ methods
    async def get_faqs(self, organization_id: str, category: Optional[str] = None) -> List[FAQ]:
        filters = [FAQ.organization_id == organization_id]
        if category:
            filters.append(FAQ.category == category)
        stmt = select(FAQ).where(*filters).order_by(FAQ.created_at.desc())
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def search_faqs(self, organization_id: str, query: str) -> List[FAQ]:
        stmt = select(FAQ).where(
            FAQ.organization_id == organization_id,
            (FAQ.question.ilike(f"%{query}%")) | (FAQ.answer.ilike(f"%{query}%"))
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())
