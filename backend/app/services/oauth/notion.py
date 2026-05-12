"""Notion OAuth 2.0 provider."""

import urllib.parse

import httpx

from app.services.oauth.base import Credentials, OAuthError, OAuthProvider

_AUTH_URL = "https://api.notion.com/v1/oauth/authorize"
_TOKEN_URL = "https://api.notion.com/v1/oauth/token"


class NotionOAuthProvider(OAuthProvider):
    """Notion OAuth 2.0 (access tokens do not expire; no refresh tokens)."""

    name = "Notion"
    app_type = "notion"

    async def get_auth_url(self, state: str, redirect_uri: str) -> str:
        """Return the Notion OAuth consent URL.

        Args:
            state:        Opaque state string.
            redirect_uri: Registered redirect URI.

        Returns:
            Fully-assembled authorisation URL.
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "owner": "user",
            "state": state,
        }
        return f"{_AUTH_URL}?{urllib.parse.urlencode(params)}"

    async def exchange_code(self, code: str, redirect_uri: str) -> Credentials:
        """Exchange a Notion authorisation code for an access token.

        Notion uses HTTP Basic auth with the client credentials, and the token
        response does not include an expiry (Notion tokens do not expire).

        Args:
            code:         Authorisation code from the callback.
            redirect_uri: Must match the URI used in :meth:`get_auth_url`.

        Returns:
            Fresh :class:`Credentials` with ``extra["workspace_id"]``.

        Raises:
            OAuthError: On non-200 response from Notion.
        """
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                _TOKEN_URL,
                json={"grant_type": "authorization_code", "code": code, "redirect_uri": redirect_uri},
                auth=(self.client_id, self.client_secret),
                headers={"Notion-Version": "2022-06-28"},
            )

        if resp.status_code != 200:
            raise OAuthError(
                f"Notion token exchange failed: {resp.text}",
                provider=self.name,
                status_code=resp.status_code,
            )

        data = resp.json()
        return Credentials(
            access_token=data["access_token"],
            token_type=data.get("token_type", "bearer"),
            # Notion tokens don't expire.
            expires_at=None,
            extra={
                "workspace_id": data.get("workspace_id", ""),
                "workspace_name": data.get("workspace_name", ""),
                "bot_id": data.get("bot_id", ""),
            },
        )

    async def refresh_token(self, credentials: Credentials) -> Credentials:
        """No-op for Notion — tokens do not expire.

        Args:
            credentials: Existing credentials.

        Returns:
            The same :class:`Credentials` unchanged.
        """
        # Notion access tokens do not expire and there is no refresh mechanism.
        return credentials
