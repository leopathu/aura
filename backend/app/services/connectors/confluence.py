"""Confluence connector — fetches pages from Atlassian Confluence via REST API v2."""

from __future__ import annotations

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

_PAGE_SIZE = 50


class ConfluenceConnector(BaseConnector):
    """Fetches Confluence pages via the Confluence Cloud REST API v2."""

    app_type = "confluence"

    async def list_items(
        self,
        credentials: Credentials,
        config: dict | None = None,
    ) -> list[ExternalItem]:
        """List all pages from the configured Confluence spaces.

        Config keys:
        - ``space_keys`` (list[str]): Space keys to sync (e.g. ``["ENG", "DOCS"]``).
          If omitted, all spaces the token can access are synced.
        - ``max_pages`` (int): Hard cap (default 500).

        Args:
            credentials: OAuth credentials (extra[``cloud_id``] required).
            config:      Per-connection filter config.

        Returns:
            List of :class:`ExternalItem` objects.
        """
        cfg = config or {}
        space_keys: list[str] = cfg.get("space_keys", [])
        max_pages: int = cfg.get("max_pages", 500)

        cloud_id = credentials.extra.get("cloud_id", "")
        if not cloud_id:
            raise ConnectorError(
                "Confluence cloud_id missing from credentials. Re-authorise the connection.",
                connector=self.app_type,
            )

        base_url = f"https://api.atlassian.com/ex/confluence/{cloud_id}/wiki/api/v2"
        headers = _auth_headers(credentials)
        items: list[ExternalItem] = []

        async with httpx.AsyncClient(timeout=30) as client:
            if space_keys:
                for key in space_keys:
                    space_items = await self._fetch_space_pages(
                        client, headers, base_url, key, max_pages - len(items)
                    )
                    items.extend(space_items)
                    if len(items) >= max_pages:
                        break
            else:
                # Discover all accessible spaces.
                space_keys_discovered = await self._list_space_keys(
                    client, headers, base_url
                )
                for key in space_keys_discovered:
                    space_items = await self._fetch_space_pages(
                        client, headers, base_url, key, max_pages - len(items)
                    )
                    items.extend(space_items)
                    if len(items) >= max_pages:
                        break

        return items

    async def fetch_item(
        self,
        credentials: Credentials,
        item_id: str,
        config: dict | None = None,
    ) -> ExternalItem:
        """Fetch a single Confluence page by its numeric ID.

        Args:
            credentials: OAuth credentials.
            item_id:     Confluence page ID (numeric string).
            config:      Unused.

        Returns:
            The fetched :class:`ExternalItem`.
        """
        cloud_id = credentials.extra.get("cloud_id", "")
        if not cloud_id:
            raise ConnectorError("Confluence cloud_id missing.", connector=self.app_type)

        base_url = f"https://api.atlassian.com/ex/confluence/{cloud_id}/wiki/api/v2"
        headers = _auth_headers(credentials)

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{base_url}/pages/{item_id}",
                headers=headers,
                params={"body-format": "storage"},
            )
            _check(resp, self.app_type)
            page = resp.json()
            item = _parse_page(page, cloud_id)
            if not item:
                raise ConnectorError(f"Could not parse Confluence page {item_id}", connector=self.app_type)
            return item

    # ------------------------------------------------------------------

    async def _list_space_keys(
        self,
        client: httpx.AsyncClient,
        headers: dict,
        base_url: str,
    ) -> list[str]:
        """Return all space keys accessible to the token."""
        keys: list[str] = []
        cursor: str | None = None
        while True:
            params: dict = {"limit": 50}
            if cursor:
                params["cursor"] = cursor
            resp = await client.get(f"{base_url}/spaces", headers=headers, params=params)
            if resp.status_code != 200:
                break
            data = resp.json()
            for sp in data.get("results", []):
                keys.append(sp.get("key", ""))
            links = data.get("_links", {})
            if not links.get("next"):
                break
            cursor = links["next"].split("cursor=")[-1] if "cursor=" in links.get("next", "") else None
            if not cursor:
                break
        return [k for k in keys if k]

    async def _fetch_space_pages(
        self,
        client: httpx.AsyncClient,
        headers: dict,
        base_url: str,
        space_key: str,
        max_count: int,
    ) -> list[ExternalItem]:
        """Fetch up to *max_count* pages from *space_key*."""
        items: list[ExternalItem] = []
        cursor: str | None = None

        while len(items) < max_count:
            params: dict = {
                "spaceKey": space_key,
                "limit": min(_PAGE_SIZE, max_count - len(items)),
                "body-format": "storage",
            }
            if cursor:
                params["cursor"] = cursor

            resp = await client.get(f"{base_url}/pages", headers=headers, params=params)
            _check(resp, self.app_type)
            data = resp.json()

            cloud_id = base_url.split("/ex/confluence/")[1].split("/")[0]
            for page in data.get("results", []):
                item = _parse_page(page, cloud_id)
                if item:
                    items.append(item)

            links = data.get("_links", {})
            if not links.get("next"):
                break
            cursor = links["next"].split("cursor=")[-1] if "cursor=" in links.get("next", "") else None
            if not cursor:
                break

        return items


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _auth_headers(credentials: Credentials) -> dict:
    return {
        "Authorization": f"Bearer {credentials.access_token}",
        "Accept": "application/json",
    }


def _check(resp: httpx.Response, connector: str) -> None:
    if resp.status_code == 401:
        raise ConnectorError("Confluence token expired or revoked.", connector=connector, status_code=401)
    if resp.status_code not in (200, 201):
        raise ConnectorError(
            f"Confluence API error {resp.status_code}: {resp.text}", connector=connector
        )


def _parse_page(page: dict, cloud_id: str) -> ExternalItem | None:
    """Convert a Confluence page dict (API v2) to an :class:`ExternalItem`."""
    page_id = page.get("id", "")
    title = page.get("title", "Untitled")

    # Body is in "storage" format (XHTML-like)
    body_storage = (page.get("body") or {}).get("storage", {}).get("value", "")
    content = html_to_text(body_storage) if body_storage else ""

    if not content.strip():
        return None

    space_key = (page.get("spaceId") or "")
    web_url = (page.get("_links") or {}).get("webui", "")
    if web_url and not web_url.startswith("http"):
        web_url = f"https://{cloud_id}.atlassian.net/wiki{web_url}"

    version = (page.get("version") or {}).get("number", "")
    author = ((page.get("version") or {}).get("createdBy") or {}).get("displayName", "")

    return ExternalItem.build(
        external_id=page_id,
        title=title,
        content=truncate(f"# {title}\n\n{content}"),
        source_url=web_url or f"https://{cloud_id}.atlassian.net/wiki",
        metadata={"space_key": space_key, "version": version, "author": author,
                  "updated_at": (page.get("version") or {}).get("createdAt", "")},
    )
