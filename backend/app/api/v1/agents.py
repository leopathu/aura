"""Agent CRUD, connection management, OAuth flow, document listing, and sync endpoints."""

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.exceptions import AuraException
from app.db.session import get_db
from app.models.user import User
from app.schemas.agent import (
    AgentConnectionCreate,
    AgentConnectionResponse,
    AgentConnectionUpdate,
    AgentCreate,
    AgentDocumentResponse,
    AgentResponse,
    AgentUpdate,
    SyncLogResponse,
    SyncStatusResponse,
)
from app.services.agent_service import AgentService
from app.services.oauth import SUPPORTED_APP_TYPES

router = APIRouter(prefix="/agents", tags=["Agents"])

# ---------------------------------------------------------------------------
# Agent CRUD
# ---------------------------------------------------------------------------


@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    payload: AgentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgentResponse:
    """Create a new Agent."""
    svc = AgentService(db)
    agent = await svc.create(current_user.id, payload)
    return AgentResponse.model_validate(agent)


@router.get("", response_model=list[AgentResponse])
async def list_agents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AgentResponse]:
    """List all Agents owned by the current user."""
    svc = AgentService(db)
    agents = await svc.list_for_user(current_user.id)
    return [AgentResponse.model_validate(a) for a in agents]


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgentResponse:
    """Fetch a single Agent."""
    try:
        svc = AgentService(db)
        agent = await svc.get(agent_id, current_user.id)
        return AgentResponse.model_validate(agent)
    except AuraException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail)


@router.patch("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: uuid.UUID,
    payload: AgentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgentResponse:
    """Update an Agent's name or description."""
    try:
        svc = AgentService(db)
        agent = await svc.update(agent_id, current_user.id, payload)
        return AgentResponse.model_validate(agent)
    except AuraException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail)


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete an Agent and all its connections and documents."""
    try:
        svc = AgentService(db)
        await svc.delete(agent_id, current_user.id)
    except AuraException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail)


# ---------------------------------------------------------------------------
# Connection CRUD
# ---------------------------------------------------------------------------


@router.post(
    "/{agent_id}/connections",
    response_model=AgentConnectionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_connection(
    agent_id: uuid.UUID,
    payload: AgentConnectionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgentConnectionResponse:
    """Add a new app connection to an Agent.

    Creating a connection does **not** start the OAuth flow.  Call
    ``GET /{agent_id}/connections/{conn_id}/oauth/start`` after creation.
    """
    try:
        svc = AgentService(db)
        conn = await svc.create_connection(agent_id, current_user.id, payload)
        return AgentConnectionResponse.from_orm_with_flags(conn)
    except AuraException as exc:
        code_to_status = {
            "AGENT_NOT_FOUND": status.HTTP_404_NOT_FOUND,
            "UNSUPPORTED_APP_TYPE": status.HTTP_422_UNPROCESSABLE_ENTITY,
        }
        raise HTTPException(
            status_code=code_to_status.get(exc.code, status.HTTP_400_BAD_REQUEST),
            detail=exc.detail,
        )


@router.get("/{agent_id}/connections", response_model=list[AgentConnectionResponse])
async def list_connections(
    agent_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AgentConnectionResponse]:
    """List all connections for an Agent."""
    try:
        svc = AgentService(db)
        connections = await svc.list_connections(agent_id, current_user.id)
        return [AgentConnectionResponse.from_orm_with_flags(c) for c in connections]
    except AuraException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail)


@router.get("/{agent_id}/connections/{conn_id}", response_model=AgentConnectionResponse)
async def get_connection(
    agent_id: uuid.UUID,
    conn_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgentConnectionResponse:
    """Fetch a single connection."""
    try:
        svc = AgentService(db)
        conn = await svc.get_connection(agent_id, conn_id, current_user.id)
        return AgentConnectionResponse.from_orm_with_flags(conn)
    except AuraException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail)


@router.patch("/{agent_id}/connections/{conn_id}", response_model=AgentConnectionResponse)
async def update_connection(
    agent_id: uuid.UUID,
    conn_id: uuid.UUID,
    payload: AgentConnectionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgentConnectionResponse:
    """Update a connection's display name, config, or sync interval."""
    try:
        svc = AgentService(db)
        conn = await svc.update_connection(agent_id, conn_id, current_user.id, payload)
        return AgentConnectionResponse.from_orm_with_flags(conn)
    except AuraException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail)


@router.delete(
    "/{agent_id}/connections/{conn_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_connection(
    agent_id: uuid.UUID,
    conn_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Disconnect an app and delete all its synced documents."""
    try:
        svc = AgentService(db)
        await svc.delete_connection(agent_id, conn_id, current_user.id)
    except AuraException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail)


# ---------------------------------------------------------------------------
# OAuth flow
# ---------------------------------------------------------------------------


@router.get("/{agent_id}/connections/{conn_id}/oauth/start")
async def oauth_start(
    agent_id: uuid.UUID,
    conn_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    """Return the OAuth authorisation URL for the connection's provider.

    The frontend should redirect the user to the returned ``url``.

    Returns:
        ``{ "url": "<provider_auth_url>" }``
    """
    try:
        svc = AgentService(db)
        url = await svc.get_oauth_start_url(agent_id, conn_id, current_user.id)
        return {"url": url}
    except AuraException as exc:
        code_to_status = {
            "AGENT_NOT_FOUND": status.HTTP_404_NOT_FOUND,
            "CONNECTION_NOT_FOUND": status.HTTP_404_NOT_FOUND,
            "APP_CREDENTIALS_MISSING": status.HTTP_422_UNPROCESSABLE_ENTITY,
        }
        raise HTTPException(
            status_code=code_to_status.get(exc.code, status.HTTP_400_BAD_REQUEST),
            detail=exc.detail,
        )


@router.get("/oauth/callback/{app_type}", include_in_schema=False)
async def oauth_callback(
    app_type: str,
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    """Handle the OAuth provider callback.

    Exchanges the authorisation *code* for tokens, encrypts and saves them,
    then redirects the user back to the frontend connection management page.

    This endpoint is called directly by the OAuth provider, so there is no
    Bearer token — authentication is handled via the signed *state*.
    """
    # Validate app_type early to avoid unnecessary DB work.
    if app_type not in SUPPORTED_APP_TYPES:
        return RedirectResponse(
            url=f"{settings.frontend_base_url}/agents?error=unsupported_provider",
            status_code=302,
        )

    svc = AgentService(db)
    try:
        agent_id, conn_id = await svc.handle_oauth_callback(
            app_type=app_type, code=code, raw_state=state
        )
        await db.commit()
        return RedirectResponse(
            url=(
                f"{settings.frontend_base_url}/agents/{agent_id}"
                f"?tab=connections&conn={conn_id}&oauth=success"
            ),
            status_code=302,
        )
    except AuraException as exc:
        await db.rollback()
        return RedirectResponse(
            url=f"{settings.frontend_base_url}/agents?error={exc.code.lower()}",
            status_code=302,
        )


# ---------------------------------------------------------------------------
# Supported providers (discovery endpoint)
# ---------------------------------------------------------------------------


@router.get("/oauth/providers")
async def list_providers() -> dict[str, list[str]]:
    """Return the list of supported OAuth ``app_type`` values."""
    return {"providers": SUPPORTED_APP_TYPES}


# ---------------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------------


@router.get("/{agent_id}/documents", response_model=list[AgentDocumentResponse])
async def list_agent_documents(
    agent_id: uuid.UUID,
    embed_status: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AgentDocumentResponse]:
    """List all documents synced into an Agent, with optional status filter."""
    try:
        svc = AgentService(db)
        docs = await svc.list_documents(agent_id, current_user.id, embed_status=embed_status)
        return [AgentDocumentResponse.model_validate(d) for d in docs]
    except AuraException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail)


# ---------------------------------------------------------------------------
# Sync — trigger, status, history
# ---------------------------------------------------------------------------


@router.post(
    "/{agent_id}/connections/{conn_id}/sync",
    status_code=status.HTTP_202_ACCEPTED,
)
async def trigger_sync(
    agent_id: uuid.UUID,
    conn_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    """Trigger an immediate manual sync for a connection.

    The sync runs in the background — this endpoint returns immediately with
    HTTP 202.  Poll ``GET /sync/status`` to track progress.

    Returns:
        ``{ "message": "Sync started.", "connection_id": "<uuid>" }``
    """
    try:
        svc = AgentService(db)
        connection = await svc.get_connection(agent_id, conn_id, current_user.id)
    except AuraException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail)

    if not connection.credentials_enc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Connection has no OAuth token. Complete the OAuth flow before syncing.",
        )

    from app.services.sync_service import sync_connection_background

    background_tasks.add_task(sync_connection_background, conn_id)
    return {"message": "Sync started.", "connection_id": str(conn_id)}


@router.get(
    "/{agent_id}/connections/{conn_id}/sync/status",
    response_model=SyncStatusResponse,
)
async def get_sync_status(
    agent_id: uuid.UUID,
    conn_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SyncStatusResponse:
    """Return the current sync status and document counts for a connection.

    Returns:
        :class:`~app.schemas.agent.SyncStatusResponse` with live counts.
    """
    try:
        svc = AgentService(db)
        connection = await svc.get_connection(agent_id, conn_id, current_user.id)
    except AuraException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail)

    from app.repositories.agent_document_repository import AgentDocumentRepository

    doc_repo = AgentDocumentRepository(db)

    all_docs = await doc_repo.list_by_connection(conn_id)
    total = len(all_docs)
    ready = sum(1 for d in all_docs if d.embed_status == "ready")
    pending = sum(1 for d in all_docs if d.embed_status in ("pending", "embedding"))
    failed = sum(1 for d in all_docs if d.embed_status == "failed")

    return SyncStatusResponse(
        connection_id=conn_id,
        sync_status=connection.sync_status,
        sync_error=connection.sync_error,
        last_synced_at=connection.last_synced_at,
        total_docs=total,
        ready_docs=ready,
        pending_docs=pending,
        failed_docs=failed,
    )


@router.get(
    "/{agent_id}/connections/{conn_id}/sync/history",
    response_model=list[SyncLogResponse],
)
async def get_sync_history(
    agent_id: uuid.UUID,
    conn_id: uuid.UUID,
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[SyncLogResponse]:
    """Return the most recent sync log entries for a connection.

    Args:
        limit: Maximum number of log entries to return (1–100, default 20).

    Returns:
        List of :class:`~app.schemas.agent.SyncLogResponse`, newest-first.
    """
    try:
        svc = AgentService(db)
        await svc.get_connection(agent_id, conn_id, current_user.id)  # ownership check
    except AuraException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail)

    from app.repositories.agent_sync_log_repository import AgentSyncLogRepository

    log_repo = AgentSyncLogRepository(db)
    logs = await log_repo.list_by_connection(conn_id, limit=limit)
    return [SyncLogResponse.model_validate(entry) for entry in logs]
