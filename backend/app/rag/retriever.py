import math
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Document, DocumentChunk, AIProvider, AIModel
from app.models_ai.factory import get_llm_provider
from app.models_ai.providers import MockAIProvider

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)

class SearchResult:
    def __init__(
        self,
        document_id: str,
        document_title: str,
        content: str,
        page: int,
        section: str,
        score: float,
        citation: str,
    ):
        self.document_id = document_id
        self.document_title = document_title
        self.content = content
        self.page = page
        self.section = section
        self.score = score
        self.citation = citation

    def to_dict(self) -> Dict[str, Any]:
        return {
            "document_id": self.document_id,
            "document_title": self.document_title,
            "content": self.content,
            "page": self.page,
            "section": self.section,
            "score": round(self.score, 4),
            "citation": self.citation,
        }

class DocumentRetriever:
    @staticmethod
    async def search(
        db: AsyncSession,
        organization_id: str,
        query: str,
        top_k: int = 5,
        min_score: float = 0.3,
        brain_id: Optional[str] = None
    ) -> List[SearchResult]:
        """
        Embeds user query and searches organization document chunks using cosine similarity.
        """
        # 1. Fetch provider for embeddings
        prov_stmt = select(AIProvider).where(
            AIProvider.organization_id == organization_id,
            AIProvider.is_active == True
        )
        prov_res = await db.execute(prov_stmt)
        provider_record = prov_res.scalar_one_or_none()
        llm = get_llm_provider(provider_record) if provider_record else MockAIProvider()

        embed_kwargs = {}
        if provider_record:
            m_stmt = select(AIModel).where(
                AIModel.provider_id == provider_record.id,
                AIModel.model_type == "EMBEDDING",
                AIModel.is_default == True
            )
            m_res = await db.execute(m_stmt)
            m_obj = m_res.scalar_one_or_none()
            if m_obj:
                embed_kwargs["model"] = m_obj.model_id

        try:
            query_vecs = await llm.embed([query], **embed_kwargs)
        except Exception:
            query_vecs = await MockAIProvider().embed([query])

        if not query_vecs:
            return []
        query_vec = query_vecs[0]

        # 2. Query all indexed document chunks in organization (and brain if specified)
        stmt = (
            select(DocumentChunk, Document.title)
            .join(Document, Document.id == DocumentChunk.document_id)
            .where(
                Document.organization_id == organization_id,
                Document.status == "INDEXED"
            )
        )
        if brain_id:
            stmt = stmt.where(Document.brain_id == brain_id)
        res = await db.execute(stmt)
        records = res.all()

        # If brain_id had no documents, fallback to org documents
        if not records and brain_id:
            fallback_stmt = (
                select(DocumentChunk, Document.title)
                .join(Document, Document.id == DocumentChunk.document_id)
                .where(
                    Document.organization_id == organization_id,
                    Document.status == "INDEXED"
                )
            )
            fallback_res = await db.execute(fallback_stmt)
            records = fallback_res.all()

        scored_results = []
        for chunk, doc_title in records:
            if chunk.embedding_vector:
                sim = cosine_similarity(query_vec, chunk.embedding_vector)
            else:
                # Basic keyword fallback
                words = set(query.lower().split())
                c_words = set(chunk.content.lower().split())
                sim = len(words.intersection(c_words)) / max(len(words), 1)

            if sim >= min_score:
                meta = chunk.metadata_json or {}
                page = meta.get("page", 1)
                sec = meta.get("section", "General")
                citation = f"{doc_title} → Page {page} ({sec})"
                scored_results.append(
                    SearchResult(
                        document_id=chunk.document_id,
                        document_title=doc_title,
                        content=chunk.content,
                        page=page,
                        section=sec,
                        score=sim,
                        citation=citation,
                    )
                )

        scored_results.sort(key=lambda x: x.score, reverse=True)
        return scored_results[:top_k]
