"""Repository for AgentConnection CRUD and sync-status operations."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decrypt_credentials, encrypt_credentials
from app.models.agent import AgentConnection
from app.schemas.agent import AgentConnectionCreate, AgentConnectionUpdate


class AgentConnectionRepository:
    """Database access layer for the AgentConnection model."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, agent_id: uuid.UUID, data: AgentConnectionCreate) -> AgentConnection:
        """Create and persist a new AgentConnection under *agent_id*.

        The user-supplied OAuth app credentials (``app_client_id`` /
        ``app_client_secret``) are encrypted before persistence.  Any initial
        OAuth access token in *data.credentials* is also encrypted.

        Args:
            agent_id: UUID of the owning Agent.
            data: Validated creation payload.

        Returns:
            The newly created AgentConnection instance.
        """
        app_credentials_enc = encrypt_credentials(
            {"client_id": data.app_client_id, "client_secret": data.app_client_secret}
        )

        credentials_enc: str | None = None
        if data.credentials:
            credentials_enc = encrypt_credentials(data.credentials)

        connection = AgentConnection(
            agent_id=agent_id,
            app_type=data.app_type,
            display_name=data.display_name,
            app_credentials_enc=app_credentials_enc,
            credentials_enc=credentials_enc,
            config_json=data.config_json,
            sync_interval_minutes=data.sync_interval_minutes,
        )
        self.db.add(connection)
        await self.db.flush()
        await self.db.refresh(connection)
        return connection

    async def get_by_id(self, connection_id: uuid.UUID) -> AgentConnection | None:
        """Fetch a single AgentConnection by primary key.

        Args:
            connection_id: UUID of the AgentConnection.

        Returns:
            The connection or *None* if not found.
        """
        result = await self.db.execute(
            select(AgentConnection).where(AgentConnection.id == connection_id)
        )
        return result.scalars().first()

    async def get_by_id_and_agent(
        self, connection_id: uuid.UUID, agent_id: uuid.UUID
    ) -> AgentConnection | None:
        """Fetch a connection while verifying it belongs to *agent_id*.

        Args:
            connection_id: UUID of the AgentConnection.
            agent_id: UUID of the owning Agent.

        Returns:
            The connection or *None* if not found or mismatched.
        """
        result = await self.db.execute(
            select(AgentConnection).where(
                AgentConnection.id == connection_id,
                AgentConnection.agent_id == agent_id,
            )
        )
        return result.scalars().first()

    async def list_by_agent(self, agent_id: uuid.UUID) -> list[AgentConnection]:
        """Return all connections for *agent_id*, ordered by creation time.

        Args:
            agent_id: UUID of the owning Agent.

        Returns:
            List of AgentConnection instances.
        """
        result = await self.db.execute(
            select(AgentConnection)
            .where(AgentConnection.agent_id == agent_id)
            .order_by(AgentConnection.created_at)
        )
        return list(result.scalars().all())

    async def update(
        self, connection: AgentConnection, data: AgentConnectionUpdate
    ) -> AgentConnection:
        """Apply non-null fields from *data* onto *connection* and flush.

        Credentials are re-encrypted when provided.

        Args:
            connection: Existing AgentConnection ORM instance.
            data: Validated update payload.

        Returns:
            The updated AgentConnection instance.
        """
        if data.display_name is not None:
            connection.display_name = data.display_name
        if data.app_client_id is not None and data.app_client_secret is not None:
            connection.app_credentials_enc = encrypt_credentials(
                {"client_id": data.app_client_id, "client_secret": data.app_client_secret}
            )
        if data.credentials is not None:
            connection.credentials_enc = encrypt_credentials(data.credentials)
        if data.config_json is not None:
            connection.config_json = data.config_json
        if data.sync_interval_minutes is not None:
            connection.sync_interval_minutes = data.sync_interval_minutes
        await self.db.flush()
        await self.db.refresh(connection)
        return connection

    async def set_sync_status(
        self,
        connection: AgentConnection,
        status: str,
        error: str | None = None,
        update_last_synced: bool = False,
    ) -> AgentConnection:
        """Update the sync lifecycle fields of *connection*.

        Args:
            connection: The AgentConnection to update.
            status: New sync_status value (e.g. "syncing", "idle", "error").
            error: Optional error message; clears the field when *None*.
            update_last_synced: When *True*, sets ``last_synced_at`` to now.

        Returns:
            The updated AgentConnection instance.
        """
        connection.sync_status = status
        connection.sync_error = error
        if update_last_synced:
            connection.last_synced_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(connection)
        return connection

    async def get_decrypted_credentials(self, connection: AgentConnection) -> dict | None:
        """Decrypt and return the stored credentials for *connection*.

        Args:
            connection: The AgentConnection whose credentials to decrypt.

        Returns:
            Decrypted credentials dictionary, or *None* if none are stored.
        """
        if not connection.credentials_enc:
            return None
        return decrypt_credentials(connection.credentials_enc)

    async def get_decrypted_app_credentials(self, connection: AgentConnection) -> dict | None:
        """Decrypt and return the user's OAuth app credentials for *connection*.

        Args:
            connection: The AgentConnection whose app credentials to decrypt.

        Returns:
            Dict with ``client_id`` and ``client_secret`` keys, or *None* if
            no app credentials have been saved yet.
        """
        if not connection.app_credentials_enc:
            return None
        return decrypt_credentials(connection.app_credentials_enc)

    async def delete(self, connection: AgentConnection) -> None:
        """Delete *connection* from the database.

        Args:
            connection: The AgentConnection instance to delete.
        """
        await self.db.delete(connection)
        await self.db.flush()
