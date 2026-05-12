"""Repository for AgentSyncLog create and list operations."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import AgentSyncLog


class AgentSyncLogRepository:
    """Database access layer for the AgentSyncLog model."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, connection_id: uuid.UUID) -> AgentSyncLog:
        """Open a new sync log entry for *connection_id* with ``started_at`` = now.

        Args:
            connection_id: UUID of the AgentConnection being synced.

        Returns:
            The newly created (in-progress) AgentSyncLog.
        """
        log = AgentSyncLog(
            connection_id=connection_id,
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(log)
        await self.db.flush()
        await self.db.refresh(log)
        return log

    async def finish(
        self,
        sync_log: AgentSyncLog,
        *,
        items_total: int = 0,
        items_new: int = 0,
        items_changed: int = 0,
        items_unchanged: int = 0,
        items_deleted: int = 0,
        items_failed: int = 0,
        error: str | None = None,
    ) -> AgentSyncLog:
        """Close a sync log entry, recording final counts and any error.

        Args:
            sync_log:        The in-progress :class:`AgentSyncLog` to close.
            items_total:     Total items returned by the connector.
            items_new:       Items created for the first time.
            items_changed:   Items re-embedded because content changed.
            items_unchanged: Items skipped (content hash matched).
            items_deleted:   Items pruned because they no longer exist upstream.
            items_failed:    Items that raised an exception during processing.
            error:           Top-level error message if the whole sync failed.

        Returns:
            The updated :class:`AgentSyncLog`.
        """
        sync_log.finished_at = datetime.now(timezone.utc)
        sync_log.items_total = items_total
        sync_log.items_new = items_new
        sync_log.items_changed = items_changed
        sync_log.items_unchanged = items_unchanged
        sync_log.items_deleted = items_deleted
        sync_log.items_failed = items_failed
        sync_log.error = error
        await self.db.flush()
        await self.db.refresh(sync_log)
        return sync_log

    async def list_by_connection(
        self,
        connection_id: uuid.UUID,
        limit: int = 20,
    ) -> list[AgentSyncLog]:
        """Return the most recent sync logs for *connection_id*.

        Args:
            connection_id: UUID of the AgentConnection.
            limit:         Maximum number of log entries to return (default 20).

        Returns:
            List of :class:`AgentSyncLog` instances ordered newest-first.
        """
        result = await self.db.execute(
            select(AgentSyncLog)
            .where(AgentSyncLog.connection_id == connection_id)
            .order_by(AgentSyncLog.started_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
