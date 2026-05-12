"""Pydantic v2 schemas for Agent, AgentConnection, AgentDocument resources, and sync."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------


class AgentCreate(BaseModel):
    """Payload for creating a new Agent."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None


class AgentUpdate(BaseModel):
    """Payload for updating an existing Agent (all fields optional)."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None


class AgentResponse(BaseModel):
    """API response shape for an Agent."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# AgentConnection
# ---------------------------------------------------------------------------


class AgentConnectionCreate(BaseModel):
    """Payload for creating a new AgentConnection under an Agent."""

    app_type: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=255)
    # User-supplied OAuth application credentials (stored encrypted, never returned).
    app_client_id: str = Field(..., min_length=1, description="Your OAuth app client ID")
    app_client_secret: str = Field(..., min_length=1, description="Your OAuth app client secret")
    config_json: str | None = None
    sync_interval_minutes: int = Field(default=60, ge=1)


class AgentConnectionUpdate(BaseModel):
    """Payload for updating an existing AgentConnection."""

    display_name: str | None = Field(default=None, min_length=1, max_length=255)
    app_client_id: str | None = Field(default=None, min_length=1)
    app_client_secret: str | None = Field(default=None, min_length=1)
    credentials: dict | None = None
    config_json: str | None = None
    sync_interval_minutes: int | None = Field(default=None, ge=1)


class AgentConnectionResponse(BaseModel):
    """API response shape for an AgentConnection.

    Encrypted secrets (``credentials_enc``, ``app_credentials_enc``) are never
    returned.  Instead two boolean flags indicate whether each secret is set.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    agent_id: uuid.UUID
    app_type: str
    display_name: str
    config_json: str | None
    sync_status: str
    sync_error: str | None
    last_synced_at: datetime | None
    sync_interval_minutes: int
    # True when the user has saved their OAuth app credentials.
    has_app_credentials: bool
    # True when the connection has gone through the OAuth flow and holds a token.
    has_oauth_token: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm_with_flags(cls, conn: object) -> "AgentConnectionResponse":
        """Build the response from an ORM instance, computing the boolean flags.

        Args:
            conn: An :class:`~app.models.agent.AgentConnection` ORM instance.

        Returns:
            Populated :class:`AgentConnectionResponse`.
        """
        from app.models.agent import AgentConnection as ORM  # avoid circular at module level

        c: ORM = conn  # type: ignore[assignment]
        return cls(
            id=c.id,
            agent_id=c.agent_id,
            app_type=c.app_type,
            display_name=c.display_name,
            config_json=c.config_json,
            sync_status=c.sync_status,
            sync_error=c.sync_error,
            last_synced_at=c.last_synced_at,
            sync_interval_minutes=c.sync_interval_minutes,
            has_app_credentials=bool(c.app_credentials_enc),
            has_oauth_token=bool(c.credentials_enc),
            created_at=c.created_at,
            updated_at=c.updated_at,
        )


# ---------------------------------------------------------------------------
# AgentDocument
# ---------------------------------------------------------------------------


class AgentDocumentResponse(BaseModel):
    """API response shape for an AgentDocument."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    agent_id: uuid.UUID
    connection_id: uuid.UUID
    external_id: str
    title: str
    source_url: str | None
    metadata_json: str | None
    content_hash: str
    embed_status: str
    embed_error: str | None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Sync status + history
# ---------------------------------------------------------------------------


class SyncStatusResponse(BaseModel):
    """Aggregated sync state for a single AgentConnection."""

    model_config = ConfigDict(from_attributes=True)

    connection_id: uuid.UUID
    sync_status: str
    sync_error: str | None
    last_synced_at: datetime | None
    total_docs: int
    ready_docs: int
    pending_docs: int
    failed_docs: int


class SyncLogResponse(BaseModel):
    """API response shape for a single AgentSyncLog entry."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    connection_id: uuid.UUID
    started_at: datetime
    finished_at: datetime | None
    items_total: int
    items_new: int
    items_changed: int
    items_unchanged: int
    items_deleted: int
    items_failed: int
    error: str | None
    created_at: datetime
