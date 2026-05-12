"""Repository for AgentChunk bulk operations and vector similarity search."""

import uuid

from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.agent import AgentChunk


class AgentChunkRepository:
    """Database access layer for the AgentChunk model."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_bulk(
        self,
        agent_document_id: uuid.UUID,
        chunks: list[dict],
    ) -> list[AgentChunk]:
        """Persist multiple chunks for an AgentDocument in one flush.

        Each entry in *chunks* must be a dict with keys ``chunk_index``,
        ``content``, and ``embedding``.

        Args:
            agent_document_id: UUID of the owning AgentDocument.
            chunks: List of chunk dicts with ``chunk_index``, ``content``,
                    and ``embedding`` (list of floats).

        Returns:
            List of newly created AgentChunk instances.
        """
        objects: list[AgentChunk] = [
            AgentChunk(
                agent_document_id=agent_document_id,
                chunk_index=chunk["chunk_index"],
                content=chunk["content"],
                embedding=chunk["embedding"],
            )
            for chunk in chunks
        ]
        self.db.add_all(objects)
        await self.db.flush()
        for obj in objects:
            await self.db.refresh(obj)
        return objects

    async def similarity_search(
        self,
        query_embedding: list[float],
        agent_id: uuid.UUID,
        top_k: int | None = None,
    ) -> list[AgentChunk]:
        """Return the *top_k* chunks most similar to *query_embedding* for *agent_id*.

        Uses cosine distance via pgvector's ``<=>`` operator.  Only chunks
        belonging to documents with ``embed_status = 'ready'`` are searched.

        Args:
            query_embedding: Query vector of dimension ``settings.vector_dimensions``.
            agent_id: UUID of the Agent to scope the search.
            top_k: Number of results to return; defaults to ``settings.retrieval_top_k``.

        Returns:
            List of AgentChunk instances ordered by ascending cosine distance
            (i.e. most similar first).
        """
        limit = top_k if top_k is not None else settings.retrieval_top_k

        # Join through AgentDocument to filter by agent and embed_status.
        from app.models.agent import AgentDocument  # local import avoids circular refs

        query_vector = str(query_embedding)
        result = await self.db.execute(
            select(AgentChunk)
            .join(AgentDocument, AgentChunk.agent_document_id == AgentDocument.id)
            .where(
                AgentDocument.agent_id == agent_id,
                AgentDocument.embed_status == "ready",
            )
            .order_by(AgentChunk.embedding.op("<=>")(query_embedding))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def delete_by_document(self, agent_document_id: uuid.UUID) -> int:
        """Delete all chunks belonging to *agent_document_id*.

        Args:
            agent_document_id: UUID of the owning AgentDocument.

        Returns:
            Number of rows deleted.
        """
        result = await self.db.execute(
            delete(AgentChunk)
            .where(AgentChunk.agent_document_id == agent_document_id)
            .returning(AgentChunk.id)
        )
        rows = result.fetchall()
        await self.db.flush()
        return len(rows)
