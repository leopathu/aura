"""Atlassian OAuth 2.0 provider (covers Jira and Confluence)."""

import time
import urllib.parse

import httpx

from app.services.oauth.base import Credentials, OAuthError, OAuthProvider

_AUTH_URL = "https://auth.atlassian.com/authorize"
_TOKEN_URL = "https://auth.atlassian.com/oauth/token"

_SCOPES = [
    "read:jira-work",
    "read:jira-user",
    "read:confluence-content.all",
    "read:confluence-space.summary",
    "offline_access",  # required for refresh tokens
]


class JiraOAuthProvider(OAuthProvider):
    """Atlassian OAuth 2.0 for Jira and Confluence (3LO)."""

    name = "Jira/Confluence"
    app_type = "jira"

    async def get_auth_url(self, state: str, redirect_uri: str) -> str:
        """Return the Atlassian OAuth consent URL.

        Args:
            state:        Opaque state string.
            redirect_uri: Registered redirect URI in your Atlassian app.

        Returns:
            Fully-assembled authorisation URL.
        """
        params = {
            "audience": "api.atlassian.com",
            "client_id": self.client_id,
            "scope": " ".join(_SCOPES),
            "redirect_uri": redirect_uri,
            "state": state,
            "response_type": "code",
            "prompt": "consent",
        }
        return f"{_AUTH_URL}?{urllib.parse.urlencode(params)}"

    async def exchange_code(self, code: str, redirect_uri: str) -> Credentials:
        """Exchange an Atlassian authorisation code for credentials.

        Args:
            code:         Authorisation code from the callback.
            redirect_uri: Must match the URI used in :meth:`get_auth_url`.

        Returns:
            Fresh :class:`Credentials` with ``extra["cloud_id"]``.

        Raises:
            OAuthError: On non-200 response from Atlassian.
        """
        payload = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(_TOKEN_URL, json=payload)

        if resp.status_code != 200:
            raise OAuthError(
                f"Atlassian token exchange failed: {resp.text}",
                provider=self.name,
                status_code=resp.status_code,
            )

        data = resp.json()

        # Fetch the accessible Atlassian cloud instance IDs.
        cloud_id = await self._fetch_cloud_id(data["access_token"])

        return Credentials(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            token_type=data.get("token_type", "Bearer"),
            expires_at=time.time() + data.get("expires_in", 3600),
            scope=data.get("scope"),
            extra={"cloud_id": cloud_id},
        )

    async def refresh_token(self, credentials: Credentials) -> Credentials:
        """Refresh Atlassian credentials.

        Args:
            credentials: Existing credentials with a valid ``refresh_token``.

        Returns:
            Updated :class:`Credentials`.

        Raises:
            OAuthError: If no refresh token is stored or Atlassian returns an error.
        """
        if not credentials.refresh_token:
            raise OAuthError("No refresh token available.", provider=self.name)

        payload = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": credentials.refresh_token,
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(_TOKEN_URL, json=payload)

        if resp.status_code != 200:
            raise OAuthError(
                f"Atlassian token refresh failed: {resp.text}",
                provider=self.name,
                status_code=resp.status_code,
            )

        data = resp.json()
        return Credentials(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token") or credentials.refresh_token,
            token_type=data.get("token_type", "Bearer"),
            expires_at=time.time() + data.get("expires_in", 3600),
            scope=data.get("scope") or credentials.scope,
            extra=credentials.extra,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    async def _fetch_cloud_id(access_token: str) -> str:
        """Fetch the first accessible Atlassian cloud site ID.

        Args:
            access_token: Freshly issued access token.

        Returns:
            Cloud site ID string, or empty string if none found.
        """
        url = "https://api.atlassian.com/oauth/token/accessible-resources"
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                url, headers={"Authorization": f"Bearer {access_token}"}
            )
        if resp.status_code == 200:
            sites = resp.json()
            if sites:
                return sites[0].get("id", "")
        return ""
