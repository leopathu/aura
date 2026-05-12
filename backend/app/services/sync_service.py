"""Sync engine — pulls data from connectors, diffs content, and updates the vector store."""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import decrypt_credentials
from app.models.agent import AgentConnection
from app.repositories.agent_chunk_repository import AgentChunkRepository
from app.repositories.agent_connection_repository import AgentConnectionRepository
from app.repositories.agent_document_repository import AgentDocumentRepository
from app.repositories.agent_sync_log_repository import AgentSyncLogRepository
from app.services.connectors import get_connector
from app.services.connectors.base import ConnectorError, ExternalItem
from app.services.embedding_service import EmbeddingService
from app.services.oauth.base import Credentials

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass
class SyncResult:
    """Counts from a completed sync run."""

    items_total: int = 0
    items_new: int = 0
    items_changed: int = 0
    items_unchanged: int = 0
    items_deleted: int = 0
    items_failed: int = 0
    error: str | None = None


# ---------------------------------------------------------------------------
# Text chunking helper
# ---------------------------------------------------------------------------


def _chunk_text(text: str, chunk_size: int = 0, overlap: int = 0) -> list[str]:
    """Split *text* into overlapping chunks of *chunk_size* characters.

    Args:
        text:       Input text to split.
        chunk_size: Maximum characters per chunk.  Defaults to
                    ``settings.chunk_size``.
        overlap:    Character overlap between consecutive chunks.  Defaults to
                    ``settings.chunk_overlap``.

    Returns:
        List of text chunks.  Returns a single-element list when *text* is
        shorter than *chunk_size*.
    """
    size = chunk_size or settings.chunk_size
    step = overlap or settings.chunk_overlap

    if len(text) <= size:
        return [text] if text.strip() else []

    chunks: list[str] = []
    start = 0
    stride = max(1, size - step)
    while start < len(text):
        chunk = text[start : start + size]
        if chunk.strip():
            chunks.append(chunk)
        start += stride

    return chunks


# ---------------------------------------------------------------------------
# Core service
# ---------------------------------------------------------------------------


class SyncService:
    """Orchestrates the full sync pipeline for a single AgentConnection.

    Steps:
        1. Mark connection as ``syncing``.
        2. Refresh OAuth token if expiring soon.
        3. Fetch all :class:`~app.services.connectors.base.ExternalItem` objects
           from the connector.
        4. Upsert :class:`~app.models.agent.AgentDocument` rows; skip unchanged
           ones (content hash match).
        5. For new or changed documents: re-chunk → re-embed → store chunks.
        6. Prune documents whose ``external_id`` no longer exists upstream.
        7. Mark connection as ``idle`` and record a
           :class:`~app.models.agent.AgentSyncLog` entry.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._connections = AgentConnectionRepository(db)
        self._documents = AgentDocumentRepository(db)
        self._chunks = AgentChunkRepository(db)
        self._logs = AgentSyncLogRepository(db)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def sync_connection(self, connection_id: uuid.UUID) -> SyncResult:
        """Run a full sync for *connection_id*.

        This method is safe to call from both API background tasks and the
        scheduler.  It handles its own error recovery: if anything raises an
        unexpected exception the connection is marked ``error`` and the
        exception is re-raised so the caller can log it.

        Args:
            connection_id: UUID of the :class:`~app.models.agent.AgentConnection`
                to sync.

        Returns:
            :class:`SyncResult` with per-category item counts.

        Raises:
            ValueError: If the connection cannot be found.
            Exception:  Any unexpected error — connection is marked ``error``
                before propagation.
        """
        connection = await self._connections.get_by_id(connection_id)
        if not connection:
            raise ValueError(f"AgentConnection {connection_id} not found.")

        # Bail out if already syncing (prevents concurrent duplicate runs).
        if connection.sync_status == "syncing":
            log.info("Connection %s is already syncing — skipping.", connection_id)
            return SyncResult()

        # Open a sync log entry.
        sync_log = await self._logs.create(connection_id)
        await self._connections.set_sync_status(connection, "syncing")
        await self._db.commit()

        result = SyncResult()
        try:
            result = await self._run_sync(connection)
        except Exception as exc:
            result.error = str(exc)
            log.exception("Sync failed for connection %s: %s", connection_id, exc)
            await self._connections.set_sync_status(
                connection, "error", error=str(exc)
            )
        else:
            await self._connections.set_sync_status(
                connection, "idle", update_last_synced=True
            )
        finally:
            await self._logs.finish(
                sync_log,
                items_total=result.items_total,
                items_new=result.items_new,
                items_changed=result.items_changed,
                items_unchanged=result.items_unchanged,
                items_deleted=result.items_deleted,
                items_failed=result.items_failed,
                error=result.error,
            )
            await self._db.commit()

        return result

    # ------------------------------------------------------------------
    # Internal pipeline
    # ------------------------------------------------------------------

    async def _run_sync(self, connection: AgentConnection) -> SyncResult:
        """Execute the main sync pipeline.

        Args:
            connection: The :class:`~app.models.agent.AgentConnection` to sync.

        Returns:
            :class:`SyncResult` with populated counters.
        """
        result = SyncResult()

        # Step 1: refresh credentials if expiring.
        from app.services.agent_service import AgentService  # local import to avoid circular

        agent_svc = AgentService(self._db)
        connection = await agent_svc.refresh_connection_credentials(connection)

        # Step 2: decrypt OAuth token.
        raw_creds = await self._connections.get_decrypted_credentials(connection)
        if not raw_creds:
            raise ConnectorError(
                "Connection has no OAuth token. Complete the OAuth flow first.",
                connector=connection.app_type,
            )
        credentials = Credentials.from_dict(raw_creds)

        # Step 3: parse config.
        config: dict | None = None
        if connection.config_json:
            try:
                config = json.loads(connection.config_json)
            except json.JSONDecodeError:
                log.warning("Connection %s has invalid config_json — ignoring.", connection.id)

        # Step 4: fetch items from connector.
        connector = get_connector(connection.app_type)
        log.info(
            "Starting sync for connection %s (app_type=%s).",
            connection.id,
            connection.app_type,
        )
        items: list[ExternalItem] = await connector.list_items(credentials, config)
        result.items_total = len(items)
        log.info("Connector returned %d items for connection %s.", len(items), connection.id)

        # Step 5: upsert each item.
        fetched_external_ids: set[str] = set()
        for item in items:
            fetched_external_ids.add(item.external_id)
            try:
                await self._process_item(
                    connection=connection,
                    item=item,
                    credentials=credentials,
                    result=result,
                )
            except Exception as exc:
                result.items_failed += 1
                log.warning(
                    "Failed to process item %s from connection %s: %s",
                    item.external_id,
                    connection.id,
                    exc,
                )

        # Step 6: prune deleted items.
        result.items_deleted = await self._prune_deleted(
            connection=connection,
            fetched_external_ids=fetched_external_ids,
        )

        return result

    async def _process_item(
        self,
        connection: AgentConnection,
        item: ExternalItem,
        credentials: Credentials,
        result: SyncResult,
    ) -> None:
        """Upsert one :class:`ExternalItem` and (re-)embed if content changed.

        Args:
            connection:  The owning AgentConnection.
            item:        The external item to persist.
            credentials: OAuth credentials (unused here but available for
                         connector fetch_item calls if needed in future).
            result:      Mutable :class:`SyncResult` — counters are incremented
                         in-place.
        """
        metadata_json = json.dumps(item.metadata) if item.metadata else None

        doc, created = await self._documents.create_or_update(
            agent_id=connection.agent_id,
            connection_id=connection.id,
            external_id=item.external_id,
            title=item.title,
            content=item.content,
            content_hash=item.content_hash,
            source_url=item.source_url,
            metadata_json=metadata_json,
        )

        if not created and doc.embed_status == "ready":
            # Content was identical — nothing to re-embed.
            result.items_unchanged += 1
            return

        if created:
            result.items_new += 1
        else:
            result.items_changed += 1

        # Delete old chunks before re-embedding.
        await self._chunks.delete_by_document(doc.id)

        # Mark as embedding in progress.
        await self._documents.set_embed_status(doc, "embedding")

        try:
            await self._embed_document(doc.id, item.content)
            await self._documents.set_embed_status(doc, "ready")
        except Exception as exc:
            await self._documents.set_embed_status(doc, "failed", error=str(exc))
            raise

    async def _embed_document(self, document_id: uuid.UUID, content: str) -> None:
        """Chunk *content* and embed all chunks, storing them in ``agent_chunks``.

        Args:
            document_id: UUID of the :class:`~app.models.agent.AgentDocument`.
            content:     Full plain-text content to chunk and embed.
        """
        text_chunks = _chunk_text(content)
        if not text_chunks:
            log.debug("Document %s has no embeddable text — skipping.", document_id)
            return

        embedding_svc = EmbeddingService()
        embeddings = await embedding_svc.embed_batch(text_chunks)

        chunk_dicts = [
            {
                "chunk_index": idx,
                "content": text,
                "embedding": emb,
            }
            for idx, (text, emb) in enumerate(zip(text_chunks, embeddings))
        ]
        await self._chunks.create_bulk(document_id, chunk_dicts)

    async def _prune_deleted(
        self,
        connection: AgentConnection,
        fetched_external_ids: set[str],
    ) -> int:
        """Delete documents that no longer exist in the external source.

        Compares the set of external IDs returned during this sync run against
        all documents currently stored for the connection and removes any that
        are no longer present upstream.

        Args:
            connection:           The owning AgentConnection.
            fetched_external_ids: Set of external IDs seen in this sync.

        Returns:
            Number of documents deleted.
        """
        existing_docs = await self._documents.list_by_connection(connection.id)
        stale_ids = [
            doc.external_id
            for doc in existing_docs
            if doc.external_id not in fetched_external_ids
        ]
        if stale_ids:
            deleted = await self._documents.delete_by_connection_and_external_ids(
                connection.id, stale_ids
            )
            log.info(
                "Pruned %d stale documents from connection %s.",
                deleted,
                connection.id,
            )
            return deleted
        return 0


# ---------------------------------------------------------------------------
# Convenience factory — creates its own session for background use
# ---------------------------------------------------------------------------


async def sync_connection_background(connection_id: uuid.UUID) -> SyncResult:
    """Run :meth:`SyncService.sync_connection` with a fresh database session.

    Intended for use in FastAPI ``BackgroundTasks`` and the APScheduler job.

    Args:
        connection_id: UUID of the AgentConnection to sync.

    Returns:
        :class:`SyncResult` from the sync run.
    """
    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        service = SyncService(db)
        return await service.sync_connection(connection_id)
