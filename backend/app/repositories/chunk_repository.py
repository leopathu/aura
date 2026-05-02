"""Repository for DocumentChunk and vector similarity search."""

import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chunk import DocumentChunk
from app.models.document import Document


class ChunkRepository:
    """Handles all DocumentChunk database queries including similarity search."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_bulk(
        self,
        document_id: uuid.UUID,
        chunks: list[tuple[int, str, list[float]]],
    ) -> list[DocumentChunk]:
        """Bulk-insert chunks with embeddings for a document.

        Args:
            document_id: UUID of the parent document.
            chunks: List of (chunk_index, content, embedding) tuples.

        Returns:
            List of persisted DocumentChunk instances.
        """
        db_chunks = [
            DocumentChunk(
                document_id=document_id,
                chunk_index=index,
                content=content,
                embedding=embedding,
            )
            for index, content, embedding in chunks
        ]
        self.db.add_all(db_chunks)
        await self.db.flush()
        return db_chunks

    async def similarity_search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
    ) -> list[tuple[DocumentChunk, Document, float]]:
        """Find the top-k most similar chunks using cosine similarity.

        Args:
            query_embedding: The embedded query vector.
            top_k: Number of results to return.

        Returns:
            List of (chunk, document, similarity_score) tuples.
        """
        result = await self.db.execute(
            select(
                DocumentChunk,
                Document,
                (1 - DocumentChunk.embedding.cosine_distance(query_embedding)).label("similarity"),
            )
            .join(Document, DocumentChunk.document_id == Document.id)
            .order_by(DocumentChunk.embedding.cosine_distance(query_embedding))
            .limit(top_k)
        )
        return [(row.DocumentChunk, row.Document, row.similarity) for row in result]

    async def delete_by_document(self, document_id: uuid.UUID) -> None:
        """Remove all chunks belonging to a document."""
        result = await self.db.execute(
            select(DocumentChunk).where(DocumentChunk.document_id == document_id)
        )
        for chunk in result.scalars().all():
            await self.db.delete(chunk)
        await self.db.flush()
