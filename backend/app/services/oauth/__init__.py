"""OAuth provider registry — maps ``app_type`` slugs to provider instances."""

from app.services.oauth.base import OAuthProvider
from app.services.oauth.github import GitHubOAuthProvider
from app.services.oauth.google import GoogleOAuthProvider
from app.services.oauth.jira import JiraOAuthProvider
from app.services.oauth.linear import LinearOAuthProvider
from app.services.oauth.notion import NotionOAuthProvider
from app.services.oauth.slack import SlackOAuthProvider

# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

# Maps every supported ``app_type`` slug to a lazily-instantiated provider.
# Add new providers here as they are implemented.
_REGISTRY: dict[str, type[OAuthProvider]] = {
    "google": GoogleOAuthProvider,
    "gdrive": GoogleOAuthProvider,  # alias — Google Drive uses the same provider
    "gmail": GoogleOAuthProvider,   # alias — Gmail uses the same provider
    "slack": SlackOAuthProvider,
    "jira": JiraOAuthProvider,
    "confluence": JiraOAuthProvider,  # alias — same Atlassian provider
    "github": GitHubOAuthProvider,
    "notion": NotionOAuthProvider,
    "linear": LinearOAuthProvider,
}

# Canonical list of supported app_type values exposed in the API.
SUPPORTED_APP_TYPES: list[str] = [
    "gdrive",
    "gmail",
    "slack",
    "jira",
    "confluence",
    "github",
    "notion",
    "linear",
]


def get_provider(app_type: str, client_id: str, client_secret: str) -> OAuthProvider:
    """Return a provider instance initialised with user-supplied OAuth app credentials.

    Args:
        app_type:      One of the strings in :data:`SUPPORTED_APP_TYPES`.
        client_id:     The user's OAuth application client ID.
        client_secret: The user's OAuth application client secret.

    Returns:
        An :class:`~app.services.oauth.base.OAuthProvider` instance.

    Raises:
        KeyError: If *app_type* is not registered.
    """
    provider_cls = _REGISTRY[app_type]
    return provider_cls(client_id=client_id, client_secret=client_secret)


__all__ = [
    "OAuthProvider",
    "SUPPORTED_APP_TYPES",
    "get_provider",
]
