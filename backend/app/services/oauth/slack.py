"""Slack OAuth 2.0 provider (v2 token rotation)."""

import time
import urllib.parse

import httpx

from app.services.oauth.base import Credentials, OAuthError, OAuthProvider

_AUTH_URL = "https://slack.com/oauth/v2/authorize"
_TOKEN_URL = "https://slack.com/api/oauth.v2.access"
_REFRESH_URL = "https://slack.com/api/tooling.tokens.rotate"

_SCOPES = [
    "channels:history",
    "channels:read",
    "files:read",
    "groups:history",
    "groups:read",
    "im:history",
    "users:read",
]


class SlackOAuthProvider(OAuthProvider):
    """Slack OAuth v2 with token rotation."""

    name = "Slack"
    app_type = "slack"

    async def get_auth_url(self, state: str, redirect_uri: str) -> str:
        """Return the Slack OAuth consent URL.

        Args:
            state:        Opaque state string.
            redirect_uri: Registered redirect URI.

        Returns:
            Fully-assembled authorisation URL.
        """
        params = {
            "client_id": self.client_id,
            "scope": ",".join(_SCOPES),
            "redirect_uri": redirect_uri,
            "state": state,
        }
        return f"{_AUTH_URL}?{urllib.parse.urlencode(params)}"

    async def exchange_code(self, code: str, redirect_uri: str) -> Credentials:
        """Exchange a Slack OAuth code for an access token.

        Args:
            code:         Authorisation code from the Slack callback.
            redirect_uri: Must match the URI used in :meth:`get_auth_url`.

        Returns:
            Fresh :class:`Credentials` with ``extra["team_id"]``.

        Raises:
            OAuthError: If Slack returns ``ok: false``.
        """
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                _TOKEN_URL,
                data={
                    "code": code,
                    "redirect_uri": redirect_uri,
                },
                auth=(self.client_id, self.client_secret),
            )

        data = resp.json()
        if not data.get("ok"):
            raise OAuthError(
                f"Slack token exchange failed: {data.get('error', 'unknown')}",
                provider=self.name,
            )

        token = data.get("access_token", "")
        team = data.get("team", {})
        return Credentials(
            access_token=token,
            # Slack v2 tokens don't expire by default (rotation is optional).
            token_type="Bearer",
            scope=data.get("scope"),
            extra={"team_id": team.get("id", ""), "team_name": team.get("name", "")},
        )

    async def refresh_token(self, credentials: Credentials) -> Credentials:
        """Rotate a Slack token using ``tooling.tokens.rotate``.

        Slack token rotation is only available for certain app configurations.
        If no ``refresh_token`` is stored, the existing credentials are returned
        unchanged (Slack tokens don't expire for most configurations).

        Args:
            credentials: Existing credentials.

        Returns:
            Refreshed or unchanged :class:`Credentials`.

        Raises:
            OAuthError: If Slack reports an error during rotation.
        """
        if not credentials.refresh_token:
            # Standard Slack bot tokens don't expire — return as-is.
            return credentials

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                _REFRESH_URL,
                data={"refresh_token": credentials.refresh_token},
                auth=(self.client_id, self.client_secret),
            )

        data = resp.json()
        if not data.get("ok"):
            raise OAuthError(
                f"Slack token rotation failed: {data.get('error', 'unknown')}",
                provider=self.name,
            )

        return Credentials(
            access_token=data.get("token", credentials.access_token),
            refresh_token=data.get("refresh_token", credentials.refresh_token),
            token_type="Bearer",
            expires_at=time.time() + data.get("exp", 0),
            scope=credentials.scope,
            extra=credentials.extra,
        )
