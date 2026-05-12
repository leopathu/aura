"""Abstract base class and shared data types for all OAuth providers."""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class Credentials:
    """Normalised OAuth token set shared across all providers.

    Attributes:
        access_token:  Short-lived bearer token.
        refresh_token: Long-lived token used to obtain new access tokens.
        token_type:    Token scheme; almost always ``"Bearer"``.
        expires_at:    Unix timestamp (float) at which the access token expires.
                       ``None`` if the provider did not return an expiry.
        scope:         Space-separated list of granted scopes (provider-dependent).
        extra:         Any provider-specific fields that should be persisted
                       (e.g. ``instance_url``, ``team_id``).
    """

    access_token: str
    refresh_token: str | None = None
    token_type: str = "Bearer"
    expires_at: float | None = None
    scope: str | None = None
    extra: dict = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def is_expired(self, buffer_seconds: int = 300) -> bool:
        """Return *True* if the access token expires within *buffer_seconds*.

        Args:
            buffer_seconds: How many seconds before actual expiry we consider
                            the token expired (default 5 minutes).
        """
        if self.expires_at is None:
            return False
        return time.time() >= (self.expires_at - buffer_seconds)

    def to_dict(self) -> dict:
        """Serialise to a plain dict suitable for :func:`~app.core.security.encrypt_credentials`."""
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "token_type": self.token_type,
            "expires_at": self.expires_at,
            "scope": self.scope,
            "extra": self.extra,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Credentials":
        """Reconstruct from a dict produced by :meth:`to_dict`."""
        return cls(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            token_type=data.get("token_type", "Bearer"),
            expires_at=data.get("expires_at"),
            scope=data.get("scope"),
            extra=data.get("extra", {}),
        )


class OAuthProvider(ABC):
    """Abstract interface that every OAuth provider must implement."""

    # Subclasses should set this to a human-readable name (e.g. "Google").
    name: str = "Unknown"
    # The ``app_type`` slug used as a discriminator in the database and URL paths.
    app_type: str = ""

    def __init__(self, client_id: str, client_secret: str) -> None:
        """Initialise the provider with the user-supplied OAuth app credentials.

        Args:
            client_id:     The OAuth application client ID provided by the user.
            client_secret: The OAuth application client secret provided by the user.
        """
        self.client_id = client_id
        self.client_secret = client_secret

    @abstractmethod
    async def get_auth_url(self, state: str, redirect_uri: str) -> str:
        """Build and return the provider's authorisation URL.

        Args:
            state:        Opaque string that the provider echoes back in the
                          callback; used to correlate the callback with a DB row.
            redirect_uri: The URL the provider should redirect back to after
                          the user grants access.

        Returns:
            Full authorisation URL to redirect the user to.
        """

    @abstractmethod
    async def exchange_code(self, code: str, redirect_uri: str) -> Credentials:
        """Exchange an authorisation *code* for a :class:`Credentials` set.

        Args:
            code:         The ``code`` query parameter from the OAuth callback.
            redirect_uri: Must match the URI used in :meth:`get_auth_url`.

        Returns:
            Fresh :class:`Credentials` for the authorised user.

        Raises:
            OAuthError: If the token exchange fails.
        """

    @abstractmethod
    async def refresh_token(self, credentials: Credentials) -> Credentials:
        """Obtain a fresh access token using *credentials.refresh_token*.

        Args:
            credentials: Existing (potentially expired) credentials.

        Returns:
            Updated :class:`Credentials` with a new ``access_token`` and
            a new ``expires_at``.

        Raises:
            OAuthError: If the refresh fails (e.g. token revoked).
        """


class OAuthError(Exception):
    """Raised when an OAuth flow step fails."""

    def __init__(self, message: str, provider: str = "", status_code: int | None = None) -> None:
        self.provider = provider
        self.status_code = status_code
        super().__init__(message)
