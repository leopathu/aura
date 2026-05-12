"""RAG pipeline service — ingestion, retrieval, and generation."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import LLMException
from app.models.ai_settings import AISettings
from app.repositories.brain_repository import BrainRepository
from app.repositories.chunk_repository import ChunkRepository
from app.repositories.document_repository import DocumentRepository
from app.schemas.document import DocumentCreate
from app.schemas.query import QueryRequest, QueryResponse, SourceChunk
from app.services.embedding_service import EmbeddingService

import openai

# Provider → base URL for LLM chat completions
_LLM_BASE_URLS: dict[str, str] = {
    "openai": "",
    "anthropic": "https://api.anthropic.com/v1",
    "google": "https://generativelanguage.googleapis.com/v1beta/openai/",
    "ollama": "",  # resolved dynamically from llm_base_url
}


def _resolve_api_key(ai_key: str, fallback: str, provider: str) -> str:
    """Return the best available API key, raising a clear error if none is usable."""
    from fastapi import HTTPException  # noqa: PLC0415

    key = ai_key or fallback
    if not key or key.startswith("sk-replace") or key == "changeme":
        raise HTTPException(
            status_code=422,
            detail=(
                f"No API key configured for provider '{provider}'. "
                "Please go to Settings and enter your API key."
            ),
        )
    return key


def _normalize_ollama_url(url: str) -> str:
    """Rewrite localhost Ollama URLs to host.docker.internal for Docker networking."""
    if not url:
        return "http://host.docker.internal:11434"
    return url.replace("localhost", "host.docker.internal").replace("127.0.0.1", "host.docker.internal")


def _build_llm_client(ai: AISettings | None) -> openai.AsyncOpenAI:
    """Build an AsyncOpenAI-compatible LLM client from user AI settings."""
    if ai is None:
        return openai.AsyncOpenAI(
            api_key=_resolve_api_key(settings.openai_api_key, "", "openai")
        )

    provider = ai.llm_provider

    if provider == "ollama":
        base_url = _normalize_ollama_url(ai.llm_base_url)
        base = base_url.rstrip("/") + "/v1"
        return openai.AsyncOpenAI(api_key="ollama", base_url=base)
    if provider == "anthropic":
        return openai.AsyncOpenAI(
            api_key=_resolve_api_key(ai.llm_api_key, settings.openai_api_key, provider),
            base_url="https://api.anthropic.com/v1",
        )
    if provider == "google":
        return openai.AsyncOpenAI(
            api_key=_resolve_api_key(ai.llm_api_key, settings.openai_api_key, provider),
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        )
    # openai
    return openai.AsyncOpenAI(
        api_key=_resolve_api_key(ai.llm_api_key, settings.openai_api_key, provider)
    )


def _build_embedding_service(ai: AISettings | None) -> EmbeddingService:
    """Build an EmbeddingService from user AI settings."""
    if ai is None:
        # No settings saved — use env defaults (OpenAI)
        api_key = settings.openai_api_key
        if not api_key or api_key.startswith("sk-replace") or api_key == "changeme":
            raise HTTPException(  # type: ignore[name-defined]
                status_code=422,
                detail=(
                    "No AI settings configured. Please go to Settings and choose your "
                    "embedding provider and model before uploading documents."
                ),
            )
        return EmbeddingService(
            provider="openai",
            model=settings.embedding_model,
            api_key=api_key,
        )
    effective_key = ai.embedding_api_key or ai.llm_api_key
    return EmbeddingService(
        provider=ai.embedding_provider,
        model=ai.embedding_model,
        api_key=effective_key if ai.embedding_provider == "ollama" else _resolve_api_key(
            effective_key, settings.openai_api_key, ai.embedding_provider
        ),
        base_url=_normalize_ollama_url(ai.embedding_base_url),
    )


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

    def __init__(self, db: AsyncSession, ai: AISettings | None = None) -> None:
        self._db = db
        self._ai = ai
        self._llm_model = (ai.llm_model if ai else None) or settings.llm_model
        self._temperature = (ai.temperature if ai else None) if ai else 0.2
        self._chunk_size = (ai.chunk_size if ai else None) or settings.chunk_size
        self._chunk_overlap = (ai.chunk_overlap if ai else None) or settings.chunk_overlap
        self._top_k = (ai.retrieval_top_k if ai else None) or settings.retrieval_top_k
        self._doc_repo = DocumentRepository(db)
        self._chunk_repo = ChunkRepository(db)
        self._brain_repo = BrainRepository(db)
        self._embedding_svc = _build_embedding_service(ai)
        self._llm_client = _build_llm_client(ai)

    # ------------------------------------------------------------------
    # Ingestion
    # ------------------------------------------------------------------

    async def ingest_document(self, payload: DocumentCreate, document_id: str | None = None) -> dict:
        """Ingest a document: chunk → embed → store.

        If document_id is provided, the document already exists (fast-upload path)
        and we only need to chunk/embed and update its status.

        Args:
            payload: Document creation data including raw content.
            document_id: Optional existing document UUID (background processing).

        Returns:
            Dict with document id and number of chunks created.
        """
        import uuid as _uuid  # noqa: PLC0415

        if document_id:
            document = await self._doc_repo.get_by_id(_uuid.UUID(document_id))
            if not document:
                raise ValueError(f"Document {document_id} not found")
        else:
            document = await self._doc_repo.create(payload)

        await self._doc_repo.set_embed_status(document.id, "processing")

        try:
            raw_chunks = _chunk_text(payload.content, self._chunk_size, self._chunk_overlap)
            embeddings = await self._embedding_svc.embed_batch(raw_chunks)

            chunk_tuples = [
                (index, content, embedding)
                for index, (content, embedding) in enumerate(zip(raw_chunks, embeddings))
            ]
            await self._chunk_repo.create_bulk(document.id, chunk_tuples)
            await self._doc_repo.set_embed_status(document.id, "ready")
        except Exception as exc:
            await self._doc_repo.set_embed_status(document.id, "failed", str(exc))
            raise

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

        # If a brain_id is specified, restrict search to that brain's documents
        document_ids = None
        if request.brain_id is not None:
            document_ids = await self._brain_repo.get_document_ids(request.brain_id)

        results = await self._chunk_repo.similarity_search(
            query_embedding, top_k=self._top_k, document_ids=document_ids
        )

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
                model=self._llm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=self._temperature,
            )
            return response.choices[0].message.content or ""
        except openai.OpenAIError as exc:
            raise LLMException(f"LLM generation failed: {exc}") from exc

    async def stream_answer(
        self,
        query: str,
        brain_id: str,
        history: list[dict[str, str]] | None = None,
    ) -> AsyncGenerator[tuple[str, list[SourceChunk]], None]:
        """Stream an LLM answer token-by-token via async generator.

        Yields:
            (token, sources) — sources only set on the first yield (empty string token).
        """
        import uuid as _uuid  # noqa: PLC0415

        query_embedding = await self._embedding_svc.embed_text(query)
        document_ids = await self._brain_repo.get_document_ids(_uuid.UUID(brain_id))

        results = await self._chunk_repo.similarity_search(
            query_embedding, top_k=self._top_k, document_ids=document_ids
        )

        sources = [
            SourceChunk(
                document_title=doc.title,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                similarity=round(similarity, 4),
            )
            for chunk, doc, similarity in results
        ]

        context = "\n\n".join(
            f"[{src.document_title} — chunk {src.chunk_index}]\n{src.content}" for src in sources
        )
        system_prompt = (
            "You are a helpful assistant. Answer the user's question using only the provided "
            "context. If the context does not contain enough information, say so clearly."
        )

        messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"})

        # First yield carries the sources metadata
        yield ("", sources)

        try:
            stream = await self._llm_client.chat.completions.create(
                model=self._llm_model,
                messages=messages,  # type: ignore[arg-type]
                temperature=self._temperature,
                stream=True,
            )
            async for chunk in stream:
                token = chunk.choices[0].delta.content or ""
                if token:
                    yield (token, [])
        except openai.OpenAIError as exc:
            raise LLMException(f"LLM streaming failed: {exc}") from exc

    async def stream_agent_answer(
        self,
        query: str,
        agent_id: str,
        history: list[dict[str, str]] | None = None,
    ) -> AsyncGenerator[tuple[str, list], None]:
        """Stream an LLM answer using agent-synced content as context.

        Retrieves the most relevant AgentChunks via vector similarity, builds a
        context prompt with source metadata, and streams the LLM response.

        Yields:
            (token, sources) — sources (list[AgentSourceChunk]) only set on first yield
            (empty string token); subsequent yields carry tokens with an empty list.
        """
        import uuid as _uuid  # noqa: PLC0415
        from sqlalchemy import select  # noqa: PLC0415
        from app.models.agent import AgentChunk, AgentDocument, AgentConnection  # noqa: PLC0415
        from app.schemas.conversation import AgentSourceChunk  # noqa: PLC0415

        agent_uuid = _uuid.UUID(agent_id)
        query_embedding = await self._embedding_svc.embed_text(query)

        # Retrieve top-k chunks via pgvector similarity search
        result = await self._db.execute(
            select(AgentChunk, AgentDocument, AgentConnection)
            .join(AgentDocument, AgentChunk.agent_document_id == AgentDocument.id)
            .join(AgentConnection, AgentDocument.agent_connection_id == AgentConnection.id)
            .where(
                AgentConnection.agent_id == agent_uuid,
                AgentDocument.embed_status == "ready",
            )
            .order_by(AgentChunk.embedding.cosine_distance(query_embedding))
            .limit(self._top_k)
        )
        rows = result.all()

        sources: list[AgentSourceChunk] = [
            AgentSourceChunk(
                document_title=doc.title,
                source_url=doc.source_url,
                app_type=conn.app_type,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                similarity=round(
                    1 - float(chunk.embedding.cosine_distance(query_embedding)), 4
                ) if chunk.embedding is not None else 0.0,
            )
            for chunk, doc, conn in rows
        ]

        context = "\n\n".join(
            f"[{src.document_title} ({src.app_type}) — chunk {src.chunk_index}]\n{src.content}"
            for src in sources
        )
        system_prompt = (
            "You are a helpful assistant with access to data synced from the user's connected apps. "
            "Answer the user's question using only the provided context. "
            "If the context does not contain enough information, say so clearly."
        )

        messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"})

        # First yield carries sources metadata with an empty token
        yield ("", sources)

        try:
            stream = await self._llm_client.chat.completions.create(
                model=self._llm_model,
                messages=messages,  # type: ignore[arg-type]
                temperature=self._temperature,
                stream=True,
            )
            async for chunk in stream:
                token = chunk.choices[0].delta.content or ""
                if token:
                    yield (token, [])
        except openai.OpenAIError as exc:
            raise LLMException(f"LLM agent streaming failed: {exc}") from exc
