"""Service layer for Agent and AgentConnection business logic, including OAuth flows."""

import base64
import json
import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AuraException
from app.core.security import decrypt_credentials, encrypt_credentials
from app.models.agent import Agent, AgentConnection, AgentDocument
from app.repositories.agent_connection_repository import AgentConnectionRepository
from app.repositories.agent_document_repository import AgentDocumentRepository
from app.repositories.agent_repository import AgentRepository
from app.schemas.agent import (
    AgentConnectionCreate,
    AgentConnectionUpdate,
    AgentCreate,
    AgentUpdate,
)
from app.services.oauth import SUPPORTED_APP_TYPES, get_provider
from app.services.oauth.base import Credentials, OAuthError

log = logging.getLogger(__name__)


class AgentService:
    """Orchestrates all Agent-level operations: CRUD, connections, and OAuth."""

    def __init__(self, db: AsyncSession) -> None:
        self._agents = AgentRepository(db)
        self._connections = AgentConnectionRepository(db)
        self._documents = AgentDocumentRepository(db)

    # ------------------------------------------------------------------
    # Agent CRUD
    # ------------------------------------------------------------------

    async def create(self, user_id: uuid.UUID, data: AgentCreate) -> Agent:
        """Create a new Agent owned by *user_id*.

        Args:
            user_id: UUID of the creating user.
            data:    Validated creation payload.

        Returns:
            Newly created Agent instance.
        """
        return await self._agents.create(user_id, data)

    async def list_for_user(self, user_id: uuid.UUID) -> list[Agent]:
        """Return all Agents belonging to *user_id*.

        Args:
            user_id: UUID of the requesting user.

        Returns:
            List of Agent instances.
        """
        return await self._agents.list_by_user(user_id)

    async def get(self, agent_id: uuid.UUID, user_id: uuid.UUID) -> Agent:
        """Fetch an Agent, verifying ownership.

        Args:
            agent_id: UUID of the target Agent.
            user_id:  UUID of the requesting user.

        Returns:
            The Agent instance.

        Raises:
            AuraException (AGENT_NOT_FOUND): If the agent does not exist or is not owned by the user.
        """
        agent = await self._agents.get_by_id_and_user(agent_id, user_id)
        if not agent:
            raise AuraException(detail="Agent not found.", code="AGENT_NOT_FOUND")
        return agent

    async def update(
        self, agent_id: uuid.UUID, user_id: uuid.UUID, data: AgentUpdate
    ) -> Agent:
        """Update an Agent's metadata.

        Args:
            agent_id: UUID of the target Agent.
            user_id:  UUID of the requesting user.
            data:     Validated update payload.

        Returns:
            The updated Agent instance.
        """
        agent = await self.get(agent_id, user_id)
        return await self._agents.update(agent, data)

    async def delete(self, agent_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Delete an Agent and all its associated data (cascade).

        Args:
            agent_id: UUID of the target Agent.
            user_id:  UUID of the requesting user.
        """
        agent = await self.get(agent_id, user_id)
        await self._agents.delete(agent)

    # ------------------------------------------------------------------
    # Connection CRUD
    # ------------------------------------------------------------------

    async def create_connection(
        self, agent_id: uuid.UUID, user_id: uuid.UUID, data: AgentConnectionCreate
    ) -> AgentConnection:
        """Create a new AgentConnection under an Agent.

        Args:
            agent_id: UUID of the parent Agent.
            user_id:  UUID of the requesting user (for ownership check).
            data:     Validated creation payload.

        Returns:
            Newly created AgentConnection instance.

        Raises:
            AuraException (UNSUPPORTED_APP_TYPE): If *data.app_type* is not supported.
        """
        if data.app_type not in SUPPORTED_APP_TYPES:
            raise AuraException(
                detail=f"Unsupported app_type '{data.app_type}'. "
                       f"Supported: {', '.join(SUPPORTED_APP_TYPES)}",
                code="UNSUPPORTED_APP_TYPE",
            )
        await self.get(agent_id, user_id)  # ownership check
        return await self._connections.create(agent_id, data)

    async def list_connections(
        self, agent_id: uuid.UUID, user_id: uuid.UUID
    ) -> list[AgentConnection]:
        """Return all connections for an Agent.

        Args:
            agent_id: UUID of the parent Agent.
            user_id:  UUID of the requesting user.

        Returns:
            List of AgentConnection instances.
        """
        await self.get(agent_id, user_id)  # ownership check
        return await self._connections.list_by_agent(agent_id)

    async def get_connection(
        self, agent_id: uuid.UUID, conn_id: uuid.UUID, user_id: uuid.UUID
    ) -> AgentConnection:
        """Fetch a connection, verifying it belongs to the agent and user.

        Args:
            agent_id: UUID of the parent Agent.
            conn_id:  UUID of the AgentConnection.
            user_id:  UUID of the requesting user.

        Returns:
            The AgentConnection instance.

        Raises:
            AuraException (CONNECTION_NOT_FOUND): If not found or mismatched.
        """
        await self.get(agent_id, user_id)  # ownership check
        connection = await self._connections.get_by_id_and_agent(conn_id, agent_id)
        if not connection:
            raise AuraException(detail="Connection not found.", code="CONNECTION_NOT_FOUND")
        return connection

    async def update_connection(
        self,
        agent_id: uuid.UUID,
        conn_id: uuid.UUID,
        user_id: uuid.UUID,
        data: AgentConnectionUpdate,
    ) -> AgentConnection:
        """Update a connection's configuration or credentials.

        Args:
            agent_id: UUID of the parent Agent.
            conn_id:  UUID of the AgentConnection.
            user_id:  UUID of the requesting user.
            data:     Validated update payload.

        Returns:
            The updated AgentConnection instance.
        """
        connection = await self.get_connection(agent_id, conn_id, user_id)
        return await self._connections.update(connection, data)

    async def delete_connection(
        self, agent_id: uuid.UUID, conn_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        """Delete a connection and all its synced documents.

        Args:
            agent_id: UUID of the parent Agent.
            conn_id:  UUID of the AgentConnection.
            user_id:  UUID of the requesting user.
        """
        connection = await self.get_connection(agent_id, conn_id, user_id)
        await self._connections.delete(connection)

    # ------------------------------------------------------------------
    # OAuth flow
    # ------------------------------------------------------------------

    async def get_oauth_start_url(
        self, agent_id: uuid.UUID, conn_id: uuid.UUID, user_id: uuid.UUID
    ) -> str:
        """Build the provider's OAuth authorisation URL and return it.

        The connection's own OAuth app credentials (``app_credentials_enc``) are
        decrypted and passed directly to the provider — no server-wide client
        credentials are required.

        Args:
            agent_id: UUID of the parent Agent.
            conn_id:  UUID of the AgentConnection (must already exist).
            user_id:  UUID of the requesting user.

        Returns:
            Authorisation URL string to redirect the user to.

        Raises:
            AuraException (APP_CREDENTIALS_MISSING): If the connection does not
                yet have OAuth app credentials saved.
        """
        connection = await self.get_connection(agent_id, conn_id, user_id)
        app_creds = await self._connections.get_decrypted_app_credentials(connection)
        if not app_creds:
            raise AuraException(
                detail="This connection has no OAuth app credentials. "
                       "Update the connection with your client_id and client_secret first.",
                code="APP_CREDENTIALS_MISSING",
            )

        provider = get_provider(
            connection.app_type,
            client_id=app_creds["client_id"],
            client_secret=app_creds["client_secret"],
        )
        state = _encode_state(agent_id=agent_id, conn_id=conn_id)
        redirect_uri = _callback_uri(connection.app_type)
        return await provider.get_auth_url(state=state, redirect_uri=redirect_uri)

    async def handle_oauth_callback(
        self, app_type: str, code: str, raw_state: str
    ) -> tuple[uuid.UUID, uuid.UUID]:
        """Complete the OAuth flow: exchange code, encrypt, and persist credentials.

        Args:
            app_type:  Provider slug (from the callback URL path).
            code:      Authorisation code from the provider.
            raw_state: State string echoed back by the provider.

        Returns:
            ``(agent_id, conn_id)`` tuple for the updated connection.

        Raises:
            AuraException (INVALID_OAUTH_STATE): If the state cannot be decoded.
            AuraException (CONNECTION_NOT_FOUND): If the connection row is missing.
            AuraException (OAUTH_EXCHANGE_FAILED): If the token exchange fails.
        """
        try:
            agent_id, conn_id = _decode_state(raw_state)
        except Exception as exc:
            raise AuraException(
                detail="Invalid or tampered OAuth state.",
                code="INVALID_OAUTH_STATE",
            ) from exc

        connection = await self._connections.get_by_id_and_agent(conn_id, agent_id)
        if not connection:
            raise AuraException(detail="Connection not found.", code="CONNECTION_NOT_FOUND")

        app_creds = await self._connections.get_decrypted_app_credentials(connection)
        if not app_creds:
            raise AuraException(
                detail="Connection has no OAuth app credentials.",
                code="APP_CREDENTIALS_MISSING",
            )

        provider = get_provider(
            app_type,
            client_id=app_creds["client_id"],
            client_secret=app_creds["client_secret"],
        )
        redirect_uri = _callback_uri(app_type)
        try:
            credentials = await provider.exchange_code(code=code, redirect_uri=redirect_uri)
        except OAuthError as exc:
            log.error("OAuth exchange failed for connection %s: %s", conn_id, exc)
            raise AuraException(
                detail=f"OAuth token exchange failed: {exc}",
                code="OAUTH_EXCHANGE_FAILED",
            ) from exc

        # Persist encrypted credentials.
        connection.credentials_enc = encrypt_credentials(credentials.to_dict())
        connection.sync_status = "idle"
        connection.sync_error = None
        await self._connections.db.flush()

        return agent_id, conn_id

    async def refresh_connection_credentials(
        self, connection: AgentConnection
    ) -> AgentConnection:
        """Refresh the OAuth access token for *connection* if it is expiring soon.

        Only performs the refresh if the stored token expires within 5 minutes.
        The refreshed credentials are re-encrypted and saved back to the row.

        Args:
            connection: The AgentConnection whose credentials to refresh.

        Returns:
            The (potentially updated) AgentConnection instance.

        Raises:
            AuraException (OAUTH_REFRESH_FAILED): If the refresh call fails.
        """
        app_creds = await self._connections.get_decrypted_app_credentials(connection)
        if not app_creds:
            return connection

        raw = await self._connections.get_decrypted_credentials(connection)
        if not raw:
            return connection

        credentials = Credentials.from_dict(raw)
        if not credentials.is_expired():
            return connection

        provider = get_provider(
            connection.app_type,
            client_id=app_creds["client_id"],
            client_secret=app_creds["client_secret"],
        )
        try:
            refreshed = await provider.refresh_token(credentials)
        except OAuthError as exc:
            log.error("OAuth refresh failed for connection %s: %s", connection.id, exc)
            raise AuraException(
                detail=f"OAuth token refresh failed: {exc}",
                code="OAUTH_REFRESH_FAILED",
            ) from exc

        connection.credentials_enc = encrypt_credentials(refreshed.to_dict())
        await self._connections.db.flush()
        return connection

    # ------------------------------------------------------------------
    # Documents
    # ------------------------------------------------------------------

    async def list_documents(
        self,
        agent_id: uuid.UUID,
        user_id: uuid.UUID,
        embed_status: str | None = None,
    ) -> list[AgentDocument]:
        """Return all synced documents for an Agent.

        Args:
            agent_id:     UUID of the Agent.
            user_id:      UUID of the requesting user.
            embed_status: Optional filter (``"pending"``, ``"ready"``, …).

        Returns:
            List of AgentDocument instances.
        """
        await self.get(agent_id, user_id)  # ownership check
        return await self._documents.list_by_agent(agent_id, embed_status=embed_status)

# ---------------------------------------------------------------------------
# State helpers (base64-encoded JSON — no DB round-trip needed in callback)
# ---------------------------------------------------------------------------


def _encode_state(agent_id: uuid.UUID, conn_id: uuid.UUID) -> str:
    """Encode agent and connection IDs into a URL-safe state string.

    Args:
        agent_id: UUID of the Agent.
        conn_id:  UUID of the AgentConnection.

    Returns:
        URL-safe base64-encoded JSON string.
    """
    payload = {"agent_id": str(agent_id), "conn_id": str(conn_id)}
    return base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()


def _decode_state(state: str) -> tuple[uuid.UUID, uuid.UUID]:
    """Decode a state string produced by :func:`_encode_state`.

    Args:
        state: URL-safe base64 string.

    Returns:
        ``(agent_id, conn_id)`` as UUIDs.

    Raises:
        ValueError: If the state is malformed.
    """
    payload = json.loads(base64.urlsafe_b64decode(state.encode()))
    return uuid.UUID(payload["agent_id"]), uuid.UUID(payload["conn_id"])


def _callback_uri(app_type: str) -> str:
    """Build the OAuth callback URI for *app_type*.

    Args:
        app_type: Provider slug.

    Returns:
        Full callback URI string.
    """
    return f"{settings.oauth_redirect_base_url}{settings.api_prefix}/agents/oauth/callback/{app_type}"
