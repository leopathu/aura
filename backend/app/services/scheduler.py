"""APScheduler setup — polls for connections due for sync every minute."""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

log = logging.getLogger(__name__)

# Module-level scheduler singleton — started/stopped by the FastAPI lifespan.
scheduler = AsyncIOScheduler(timezone="UTC")


async def _poll_due_connections() -> None:
    """Check all AgentConnections that are due for a sync and launch them.

    A connection is *due* when:
    - Its ``sync_status`` is ``idle`` or ``error`` (not already syncing).
    - Its ``last_synced_at`` is ``None`` **or** more than
      ``sync_interval_minutes`` minutes ago.

    Each due connection is synced in its own isolated async task so that a
    slow or failing connection does not block others.
    """
    from sqlalchemy import select

    from app.db.session import AsyncSessionLocal
    from app.models.agent import AgentConnection
    from app.services.sync_service import sync_connection_background

    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(AgentConnection.id, AgentConnection.sync_interval_minutes,
                       AgentConnection.last_synced_at, AgentConnection.sync_status)
                .where(AgentConnection.sync_status.in_(["idle", "error"]))
                .where(AgentConnection.credentials_enc.is_not(None))
            )
            rows = result.fetchall()

        now = datetime.now(timezone.utc)
        due: list[uuid.UUID] = []
        for conn_id, interval, last_synced, status in rows:
            if last_synced is None:
                due.append(conn_id)
            else:
                # Ensure last_synced is timezone-aware for comparison.
                if last_synced.tzinfo is None:
                    last_synced = last_synced.replace(tzinfo=timezone.utc)
                if now - last_synced >= timedelta(minutes=interval):
                    due.append(conn_id)

        if due:
            log.info("Scheduler: %d connection(s) due for sync.", len(due))
            tasks = [
                asyncio.create_task(
                    _safe_sync(conn_id),
                    name=f"sync-{conn_id}",
                )
                for conn_id in due
            ]
            # Fire-and-forget — the tasks run concurrently in the background.
            # Results (and exceptions) are captured inside _safe_sync.
            _ = tasks  # keep references alive; they self-manage via create_task

    except Exception:
        log.exception("Scheduler: error while polling for due connections.")


async def _safe_sync(connection_id: uuid.UUID) -> None:
    """Wrapper around :func:`sync_connection_background` that swallows exceptions.

    All errors are already recorded by :class:`~app.services.sync_service.SyncService`
    on the connection row and sync log.  This wrapper simply prevents an
    unhandled exception from crashing the scheduler task.

    Args:
        connection_id: UUID of the AgentConnection to sync.
    """
    from app.services.sync_service import sync_connection_background

    try:
        result = await sync_connection_background(connection_id)
        log.info(
            "Scheduler sync complete for connection %s: "
            "new=%d changed=%d unchanged=%d deleted=%d failed=%d",
            connection_id,
            result.items_new,
            result.items_changed,
            result.items_unchanged,
            result.items_deleted,
            result.items_failed,
        )
    except Exception:
        log.exception("Scheduler: unhandled error syncing connection %s.", connection_id)


def start_scheduler() -> None:
    """Start the APScheduler and register the sync-poll job.

    Safe to call multiple times — will not add duplicate jobs.  Should be
    invoked from the FastAPI application lifespan startup handler.
    """
    if not scheduler.running:
        scheduler.add_job(
            _poll_due_connections,
            trigger=IntervalTrigger(minutes=1),
            id="sync_poll",
            replace_existing=True,
            misfire_grace_time=30,
        )
        scheduler.start()
        log.info("Sync scheduler started.")


def stop_scheduler() -> None:
    """Gracefully shut down the scheduler.

    Should be invoked from the FastAPI application lifespan shutdown handler.
    """
    if scheduler.running:
        scheduler.shutdown(wait=False)
        log.info("Sync scheduler stopped.")
