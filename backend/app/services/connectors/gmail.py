"""Gmail connector — fetches emails (subject + decoded body) from inbox or a label."""

from __future__ import annotations

import base64
import logging

import httpx

from app.services.connectors.base import (
    BaseConnector,
    ConnectorError,
    ExternalItem,
    html_to_text,
    truncate,
)
from app.services.oauth.base import Credentials

log = logging.getLogger(__name__)

_API = "https://gmail.googleapis.com/gmail/v1/users/me"
_PAGE_SIZE = 50


class GmailConnector(BaseConnector):
    """Fetches emails from Gmail via the Gmail REST API v1."""

    app_type = "gmail"

    async def list_items(
        self,
        credentials: Credentials,
        config: dict | None = None,
    ) -> list[ExternalItem]:
        """List and fetch emails matching the configured label / query.

        Config keys:
        - ``label`` (str): Gmail label ID or name (default ``"INBOX"``).
        - ``query`` (str): Raw Gmail search query string (e.g. ``"is:unread"``).
        - ``max_emails`` (int): Hard cap (default 200).
        - ``max_days`` (int): Only emails newer than this many days.

        Args:
            credentials: OAuth credentials with Gmail read scope.
            config:      Per-connection filter config.

        Returns:
            List of :class:`ExternalItem` objects, one per email.
        """
        cfg = config or {}
        label: str = cfg.get("label", "INBOX")
        query_extra: str = cfg.get("query", "")
        max_emails: int = cfg.get("max_emails", 200)
        max_days: int | None = cfg.get("max_days")

        query_parts: list[str] = [f"label:{label}"]
        if max_days:
            query_parts.append(f"newer_than:{max_days}d")
        if query_extra:
            query_parts.append(query_extra)
        query = " ".join(query_parts)

        headers = {"Authorization": f"Bearer {credentials.access_token}"}
        message_ids: list[str] = []
        page_token: str | None = None

        async with httpx.AsyncClient(timeout=30) as client:
            # Step 1: collect message IDs.
            while len(message_ids) < max_emails:
                params: dict = {
                    "q": query,
                    "maxResults": min(_PAGE_SIZE, max_emails - len(message_ids)),
                }
                if page_token:
                    params["pageToken"] = page_token

                resp = await client.get(f"{_API}/messages", headers=headers, params=params)
                _check(resp, self.app_type)

                data = resp.json()
                message_ids += [m["id"] for m in data.get("messages", [])]
                page_token = data.get("nextPageToken")
                if not page_token:
                    break

            # Step 2: fetch each message's full payload.
            items: list[ExternalItem] = []
            for msg_id in message_ids:
                try:
                    item = await self._fetch_message(client, headers, msg_id)
                    if item:
                        items.append(item)
                except Exception as exc:
                    log.warning("Gmail: skipping message %s — %s", msg_id, exc)

        return items

    async def fetch_item(
        self,
        credentials: Credentials,
        item_id: str,
        config: dict | None = None,
    ) -> ExternalItem:
        """Fetch a single Gmail message by its ID.

        Args:
            credentials: OAuth credentials.
            item_id:     Gmail message ID.
            config:      Unused.

        Returns:
            The fetched :class:`ExternalItem`.
        """
        headers = {"Authorization": f"Bearer {credentials.access_token}"}
        async with httpx.AsyncClient(timeout=30) as client:
            item = await self._fetch_message(client, headers, item_id)
            if not item:
                raise ConnectorError(f"Could not parse message {item_id}", connector=self.app_type)
            return item

    # ------------------------------------------------------------------

    async def _fetch_message(
        self,
        client: httpx.AsyncClient,
        headers: dict,
        msg_id: str,
    ) -> ExternalItem | None:
        resp = await client.get(
            f"{_API}/messages/{msg_id}",
            headers=headers,
            params={"format": "full"},
        )
        _check(resp, self.app_type)
        msg = resp.json()

        header_map = {
            h["name"].lower(): h["value"]
            for h in msg.get("payload", {}).get("headers", [])
        }
        subject = header_map.get("subject", "(no subject)")
        sender = header_map.get("from", "")
        date = header_map.get("date", "")

        body = _extract_body(msg.get("payload", {}))
        if not body.strip():
            return None

        snippet = msg.get("snippet", "")
        content = f"From: {sender}\nDate: {date}\nSubject: {subject}\n\n{body}"

        return ExternalItem.build(
            external_id=msg_id,
            title=subject,
            content=truncate(content),
            source_url=f"https://mail.google.com/mail/u/0/#inbox/{msg_id}",
            metadata={"sender": sender, "date": date, "snippet": snippet},
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _check(resp: httpx.Response, connector: str) -> None:
    if resp.status_code == 401:
        raise ConnectorError("Gmail token expired or revoked.", connector=connector, status_code=401)
    if resp.status_code != 200:
        raise ConnectorError(f"Gmail API error {resp.status_code}: {resp.text}", connector=connector)


def _decode_b64(data: str) -> str:
    """Decode URL-safe base64, returning empty string on failure."""
    try:
        return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")
    except Exception:
        return ""


def _extract_body(payload: dict) -> str:
    """Recursively extract the plain-text (or HTML-fallback) body from a message payload."""
    mime = payload.get("mimeType", "")
    body_data: str = payload.get("body", {}).get("data", "")

    if mime == "text/plain" and body_data:
        return _decode_b64(body_data)

    if mime == "text/html" and body_data:
        return html_to_text(_decode_b64(body_data))

    # Multipart — recurse into parts, prefer plain over html.
    parts = payload.get("parts", [])
    plain = ""
    html_fallback = ""
    for part in parts:
        result = _extract_body(part)
        if part.get("mimeType") == "text/plain" and result:
            plain = result
        elif part.get("mimeType") == "text/html" and result:
            html_fallback = result
        elif result:
            plain = plain or result

    return plain or html_fallback
