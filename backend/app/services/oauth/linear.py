"""Linear OAuth 2.0 provider."""

import time
import urllib.parse

import httpx

from app.services.oauth.base import Credentials, OAuthError, OAuthProvider

_AUTH_URL = "https://linear.app/oauth/authorize"
_TOKEN_URL = "https://api.linear.app/oauth/token"
_REVOKE_URL = "https://api.linear.app/oauth/revoke"

_SCOPES = ["read"]


class LinearOAuthProvider(OAuthProvider):
    """Linear OAuth 2.0 provider."""

    name = "Linear"
    app_type = "linear"

    async def get_auth_url(self, state: str, redirect_uri: str) -> str:
        """Return the Linear OAuth consent URL.

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
            "scope": ",".join(_SCOPES),
            "state": state,
        }
        return f"{_AUTH_URL}?{urllib.parse.urlencode(params)}"

    async def exchange_code(self, code: str, redirect_uri: str) -> Credentials:
        """Exchange a Linear authorisation code for an access token.

        Args:
            code:         Authorisation code from the callback.
            redirect_uri: Must match the URI used in :meth:`get_auth_url`.

        Returns:
            Fresh :class:`Credentials`.

        Raises:
            OAuthError: On non-200 response from Linear.
        """
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                _TOKEN_URL,
                data={
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "grant_type": "authorization_code",
                },
            )

        if resp.status_code != 200:
            raise OAuthError(
                f"Linear token exchange failed: {resp.text}",
                provider=self.name,
                status_code=resp.status_code,
            )

        data = resp.json()
        return Credentials(
            access_token=data["access_token"],
            token_type=data.get("token_type", "Bearer"),
            # Linear tokens expire after 10 years; no practical expiry handling needed.
            expires_at=time.time() + data.get("expires_in", 315360000),
            scope=data.get("scope"),
        )

    async def refresh_token(self, credentials: Credentials) -> Credentials:
        """No-op for Linear — access tokens are long-lived (10 years).

        Linear does not support refresh tokens. If a token is revoked, the user
        must re-authorise.

        Args:
            credentials: Existing credentials.

        Returns:
            The same :class:`Credentials` unchanged.
        """
        return credentials
