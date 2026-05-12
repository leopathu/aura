"""Repository for AgentDocument upsert and lifecycle operations."""

import uuid

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import AgentDocument


class AgentDocumentRepository:
    """Database access layer for the AgentDocument model."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_or_update(
        self,
        agent_id: uuid.UUID,
        connection_id: uuid.UUID,
        external_id: str,
        title: str,
        content: str,
        content_hash: str,
        source_url: str | None = None,
        metadata_json: str | None = None,
    ) -> tuple[AgentDocument, bool]:
        """Upsert an AgentDocument by (connection_id, external_id).

        If a document with the same *connection_id* + *external_id* already
        exists and the *content_hash* has changed, the content fields are
        updated and ``embed_status`` is reset to "pending" so it gets
        re-embedded.  If the hash is unchanged, the existing row is returned
        as-is.

        Args:
            agent_id: UUID of the owning Agent.
            connection_id: UUID of the source AgentConnection.
            external_id: Unique identifier from the external app.
            title: Document title.
            content: Full text content.
            content_hash: SHA-256 hex digest of *content*.
            source_url: Optional URL back to the original document.
            metadata_json: Optional JSON string with additional metadata.

        Returns:
            A ``(document, created)`` tuple where *created* is True for new
            rows and False for existing ones.
        """
        existing = await self.get_by_connection_and_external_id(connection_id, external_id)
        if existing is not None:
            if existing.content_hash == content_hash:
                # Unchanged — nothing to do.
                return existing, False
            # Content changed — update and reset embed pipeline.
            existing.title = title
            existing.content = content
            existing.content_hash = content_hash
            existing.source_url = source_url
            existing.metadata_json = metadata_json
            existing.embed_status = "pending"
            existing.embed_error = None
            await self.db.flush()
            await self.db.refresh(existing)
            return existing, False

        doc = AgentDocument(
            agent_id=agent_id,
            connection_id=connection_id,
            external_id=external_id,
            title=title,
            content=content,
            content_hash=content_hash,
            source_url=source_url,
            metadata_json=metadata_json,
        )
        self.db.add(doc)
        await self.db.flush()
        await self.db.refresh(doc)
        return doc, True

    async def get_by_id(self, document_id: uuid.UUID) -> AgentDocument | None:
        """Fetch a single AgentDocument by primary key.

        Args:
            document_id: UUID of the AgentDocument.

        Returns:
            The document or *None* if not found.
        """
        result = await self.db.execute(
            select(AgentDocument).where(AgentDocument.id == document_id)
        )
        return result.scalars().first()

    async def get_by_connection_and_external_id(
        self, connection_id: uuid.UUID, external_id: str
    ) -> AgentDocument | None:
        """Fetch a document by its (connection_id, external_id) natural key.

        Args:
            connection_id: UUID of the source AgentConnection.
            external_id: Identifier from the external app.

        Returns:
            The document or *None* if not found.
        """
        result = await self.db.execute(
            select(AgentDocument).where(
                AgentDocument.connection_id == connection_id,
                AgentDocument.external_id == external_id,
            )
        )
        return result.scalars().first()

    async def list_by_agent(
        self,
        agent_id: uuid.UUID,
        embed_status: str | None = None,
    ) -> list[AgentDocument]:
        """Return documents belonging to *agent_id*, optionally filtered by status.

        Args:
            agent_id: UUID of the owning Agent.
            embed_status: Optional filter (e.g. "pending", "ready", "failed").

        Returns:
            List of AgentDocument instances ordered by creation time.
        """
        query = select(AgentDocument).where(AgentDocument.agent_id == agent_id)
        if embed_status is not None:
            query = query.where(AgentDocument.embed_status == embed_status)
        result = await self.db.execute(query.order_by(AgentDocument.created_at))
        return list(result.scalars().all())

    async def list_by_connection(
        self,
        connection_id: uuid.UUID,
        embed_status: str | None = None,
    ) -> list[AgentDocument]:
        """Return documents for a given *connection_id*.

        Args:
            connection_id: UUID of the AgentConnection.
            embed_status: Optional embed-status filter.

        Returns:
            List of AgentDocument instances ordered by creation time.
        """
        query = select(AgentDocument).where(AgentDocument.connection_id == connection_id)
        if embed_status is not None:
            query = query.where(AgentDocument.embed_status == embed_status)
        result = await self.db.execute(query.order_by(AgentDocument.created_at))
        return list(result.scalars().all())

    async def set_embed_status(
        self,
        document: AgentDocument,
        status: str,
        error: str | None = None,
    ) -> AgentDocument:
        """Update the embedding pipeline status fields.

        Args:
            document: The AgentDocument to update.
            status: New embed_status value ("pending", "embedding", "ready", "failed").
            error: Optional error message; clears the field when *None*.

        Returns:
            The updated AgentDocument instance.
        """
        document.embed_status = status
        document.embed_error = error
        await self.db.flush()
        await self.db.refresh(document)
        return document

    async def delete(self, document: AgentDocument) -> None:
        """Delete *document* from the database.

        Args:
            document: The AgentDocument instance to delete.
        """
        await self.db.delete(document)
        await self.db.flush()

    async def delete_by_connection_and_external_ids(
        self,
        connection_id: uuid.UUID,
        external_ids: list[str],
    ) -> int:
        """Bulk-delete documents for *connection_id* whose external_id is in *external_ids*.

        Used to prune documents that have been deleted in the external app.

        Args:
            connection_id: UUID of the source AgentConnection.
            external_ids: List of external IDs to remove.

        Returns:
            Number of rows deleted.
        """
        if not external_ids:
            return 0
        result = await self.db.execute(
            delete(AgentDocument)
            .where(
                AgentDocument.connection_id == connection_id,
                AgentDocument.external_id.in_(external_ids),
            )
            .returning(AgentDocument.id)
        )
        rows = result.fetchall()
        await self.db.flush()
        return len(rows)
