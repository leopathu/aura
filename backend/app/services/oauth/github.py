"""GitHub OAuth 2.0 provider."""

import time
import urllib.parse

import httpx

from app.services.oauth.base import Credentials, OAuthError, OAuthProvider

_AUTH_URL = "https://github.com/login/oauth/authorize"
_TOKEN_URL = "https://github.com/login/oauth/access_token"

_SCOPES = ["repo", "read:org", "read:user"]


class GitHubOAuthProvider(OAuthProvider):
    """GitHub OAuth 2.0 (non-expiring tokens, or fine-grained PAT refresh)."""

    name = "GitHub"
    app_type = "github"

    async def get_auth_url(self, state: str, redirect_uri: str) -> str:
        """Return the GitHub OAuth consent URL.

        Args:
            state:        Opaque state string.
            redirect_uri: Registered callback URI.

        Returns:
            Fully-assembled authorisation URL.
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "scope": " ".join(_SCOPES),
            "state": state,
        }
        return f"{_AUTH_URL}?{urllib.parse.urlencode(params)}"

    async def exchange_code(self, code: str, redirect_uri: str) -> Credentials:
        """Exchange a GitHub OAuth code for an access token.

        Args:
            code:         Authorisation code from the callback.
            redirect_uri: Must match the URI used in :meth:`get_auth_url`.

        Returns:
            Fresh :class:`Credentials`.

        Raises:
            OAuthError: If GitHub returns an error.
        """
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                _TOKEN_URL,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri,
                },
                headers={"Accept": "application/json"},
            )

        data = resp.json()
        if "error" in data:
            raise OAuthError(
                f"GitHub token exchange failed: {data.get('error_description', data['error'])}",
                provider=self.name,
            )

        return Credentials(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            token_type=data.get("token_type", "Bearer"),
            # GitHub classic tokens don't expire; expiring tokens include expires_in.
            expires_at=time.time() + data["expires_in"] if "expires_in" in data else None,
            scope=data.get("scope"),
        )

    async def refresh_token(self, credentials: Credentials) -> Credentials:
        """Refresh a GitHub token (only for GitHub Apps with expiring tokens).

        Classic OAuth tokens do not expire; in that case the existing credentials
        are returned unchanged.

        Args:
            credentials: Existing credentials.

        Returns:
            Refreshed or unchanged :class:`Credentials`.

        Raises:
            OAuthError: If the refresh request fails.
        """
        if not credentials.refresh_token:
            # Classic OAuth token — does not expire.
            return credentials

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                _TOKEN_URL,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "grant_type": "refresh_token",
                    "refresh_token": credentials.refresh_token,
                },
                headers={"Accept": "application/json"},
            )

        data = resp.json()
        if "error" in data:
            raise OAuthError(
                f"GitHub token refresh failed: {data.get('error_description', data['error'])}",
                provider=self.name,
            )

        return Credentials(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token", credentials.refresh_token),
            token_type=data.get("token_type", "Bearer"),
            expires_at=time.time() + data["expires_in"] if "expires_in" in data else None,
            scope=data.get("scope") or credentials.scope,
        )
