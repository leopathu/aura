"""RAG pipeline service — ingestion, retrieval, and generation."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import LLMException
from app.repositories.chunk_repository import ChunkRepository
from app.repositories.document_repository import DocumentRepository
from app.schemas.document import DocumentCreate
from app.schemas.query import QueryRequest, QueryResponse, SourceChunk
from app.services.embedding_service import EmbeddingService

import openai


def _chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Split text into overlapping chunks by character count.

    Args:
        text: The full document text.
        chunk_size: Maximum characters per chunk.
        overlap: Number of overlapping characters between chunks.

    Returns:
        List of text chunks.
    """
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


class RAGService:
    """Orchestrates the full RAG pipeline: ingestion, retrieval, and generation."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._doc_repo = DocumentRepository(db)
        self._chunk_repo = ChunkRepository(db)
        self._embedding_svc = EmbeddingService()
        self._llm_client = openai.AsyncOpenAI(api_key=settings.openai_api_key)

    # ------------------------------------------------------------------
    # Ingestion
    # ------------------------------------------------------------------

    async def ingest_document(self, payload: DocumentCreate) -> dict:
        """Ingest a document: chunk → embed → store.

        Args:
            payload: Document creation data including raw content.

        Returns:
            Dict with document id and number of chunks created.
        """
        document = await self._doc_repo.create(payload)

        raw_chunks = _chunk_text(payload.content, settings.chunk_size, settings.chunk_overlap)
        embeddings = await self._embedding_svc.embed_batch(raw_chunks)

        chunk_tuples = [
            (index, content, embedding)
            for index, (content, embedding) in enumerate(zip(raw_chunks, embeddings))
        ]
        await self._chunk_repo.create_bulk(document.id, chunk_tuples)

        return {"document_id": str(document.id), "chunks_created": len(chunk_tuples)}

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    async def query(self, request: QueryRequest) -> QueryResponse:
        """Run the full RAG pipeline for a user query.

        Args:
            request: The query request with the user's question.

        Returns:
            QueryResponse with the generated answer and source chunks.
        """
        query_embedding = await self._embedding_svc.embed_text(request.query)
        results = await self._chunk_repo.similarity_search(query_embedding, top_k=request.top_k)

        sources = [
            SourceChunk(
                document_title=doc.title,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                similarity=round(similarity, 4),
            )
            for chunk, doc, similarity in results
        ]

        answer = await self._generate_answer(request.query, sources)
        return QueryResponse(answer=answer, sources=sources)

    # ------------------------------------------------------------------
    # Generation
    # ------------------------------------------------------------------

    async def _generate_answer(self, query: str, sources: list[SourceChunk]) -> str:
        """Call the LLM with the retrieved context to generate an answer.

        Args:
            query: The user's original question.
            sources: Retrieved source chunks to use as context.

        Returns:
            The generated answer string.

        Raises:
            LLMException: If the LLM API call fails.
        """
        context = "\n\n".join(
            f"[{src.document_title} — chunk {src.chunk_index}]\n{src.content}" for src in sources
        )
        system_prompt = (
            "You are a helpful assistant. Answer the user's question using only the provided "
            "context. If the context does not contain enough information, say so clearly."
        )
        user_prompt = f"Context:\n{context}\n\nQuestion: {query}"

        try:
            response = await self._llm_client.chat.completions.create(
                model=settings.llm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
            )
            return response.choices[0].message.content or ""
        except openai.OpenAIError as exc:
            raise LLMException(f"LLM generation failed: {exc}") from exc
