"""Google OAuth 2.0 provider (covers both Gmail and Google Drive)."""

import time
import urllib.parse

import httpx

from app.services.oauth.base import Credentials, OAuthError, OAuthProvider

_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_TOKEN_URL = "https://oauth2.googleapis.com/token"

# Scopes for read-only access to Gmail and Drive.
_SCOPES = [
    "openid",
    "email",
    "profile",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]


class GoogleOAuthProvider(OAuthProvider):
    """OAuth 2.0 PKCE-free flow for Google (server-side confidential client)."""

    name = "Google"
    app_type = "google"

    async def get_auth_url(self, state: str, redirect_uri: str) -> str:
        """Return the Google OAuth consent screen URL.

        Args:
            state:        Opaque state string echoed back by Google.
            redirect_uri: Registered redirect URI.

        Returns:
            Fully-assembled authorisation URL string.
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(_SCOPES),
            "state": state,
            "access_type": "offline",
            "prompt": "consent",  # force refresh_token on every authorisation
        }
        return f"{_AUTH_URL}?{urllib.parse.urlencode(params)}"

    async def exchange_code(self, code: str, redirect_uri: str) -> Credentials:
        """Exchange an authorisation code for Google credentials.

        Args:
            code:         Authorisation code from the OAuth callback.
            redirect_uri: Must match the URI used in :meth:`get_auth_url`.

        Returns:
            Fresh :class:`Credentials`.

        Raises:
            OAuthError: If Google returns a non-200 response.
        """
        payload = {
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(_TOKEN_URL, data=payload)

        if resp.status_code != 200:
            raise OAuthError(
                f"Google token exchange failed: {resp.text}",
                provider=self.name,
                status_code=resp.status_code,
            )

        data = resp.json()
        return Credentials(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            token_type=data.get("token_type", "Bearer"),
            expires_at=time.time() + data.get("expires_in", 3600),
            scope=data.get("scope"),
        )

    async def refresh_token(self, credentials: Credentials) -> Credentials:
        """Use the stored refresh token to obtain a new access token.

        Args:
            credentials: Existing credentials whose ``refresh_token`` is set.

        Returns:
            Updated :class:`Credentials`.

        Raises:
            OAuthError: If Google returns an error or no refresh token is stored.
        """
        if not credentials.refresh_token:
            raise OAuthError("No refresh token available.", provider=self.name)

        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": credentials.refresh_token,
            "grant_type": "refresh_token",
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(_TOKEN_URL, data=payload)

        if resp.status_code != 200:
            raise OAuthError(
                f"Google token refresh failed: {resp.text}",
                provider=self.name,
                status_code=resp.status_code,
            )

        data = resp.json()
        return Credentials(
            access_token=data["access_token"],
            # Google may not return a new refresh_token — keep the old one.
            refresh_token=data.get("refresh_token") or credentials.refresh_token,
            token_type=data.get("token_type", "Bearer"),
            expires_at=time.time() + data.get("expires_in", 3600),
            scope=data.get("scope") or credentials.scope,
        )
