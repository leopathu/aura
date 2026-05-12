"""Notion connector — fetches pages and database rows via the Notion REST API."""

from __future__ import annotations

import logging

import httpx

from app.services.connectors.base import (
    BaseConnector,
    ConnectorError,
    ExternalItem,
    truncate,
)
from app.services.oauth.base import Credentials

log = logging.getLogger(__name__)

_API = "https://api.notion.com/v1"
_NOTION_VERSION = "2022-06-28"
_PAGE_SIZE = 100


class NotionConnector(BaseConnector):
    """Fetches Notion pages and database rows via the Notion REST API."""

    app_type = "notion"

    async def list_items(
        self,
        credentials: Credentials,
        config: dict | None = None,
    ) -> list[ExternalItem]:
        """Search for all pages accessible to the integration.

        Config keys:
        - ``max_pages`` (int): Hard cap (default 500).
        - ``query`` (str): Optional Notion search query to filter pages.

        Args:
            credentials: OAuth credentials with ``read_content`` scope.
            config:      Per-connection filter config.

        Returns:
            List of :class:`ExternalItem` objects.
        """
        cfg = config or {}
        max_pages: int = cfg.get("max_pages", 500)
        query: str = cfg.get("query", "")

        headers = _auth_headers(credentials)
        items: list[ExternalItem] = []
        cursor: str | None = None

        async with httpx.AsyncClient(timeout=30) as client:
            while len(items) < max_pages:
                payload: dict = {
                    "filter": {"value": "page", "property": "object"},
                    "page_size": min(_PAGE_SIZE, max_pages - len(items)),
                }
                if query:
                    payload["query"] = query
                if cursor:
                    payload["start_cursor"] = cursor

                resp = await client.post(f"{_API}/search", headers=headers, json=payload)
                _check(resp, self.app_type)
                data = resp.json()

                for page in data.get("results", []):
                    try:
                        item = await self._fetch_page_content(client, headers, page)
                        if item:
                            items.append(item)
                    except Exception as exc:
                        log.warning("Notion: skipping page %s — %s", page.get("id"), exc)

                if data.get("has_more"):
                    cursor = data.get("next_cursor")
                else:
                    break

        return items

    async def fetch_item(
        self,
        credentials: Credentials,
        item_id: str,
        config: dict | None = None,
    ) -> ExternalItem:
        """Fetch a single Notion page by its ID.

        Args:
            credentials: OAuth credentials.
            item_id:     Notion page UUID.
            config:      Unused.

        Returns:
            The fetched :class:`ExternalItem`.
        """
        headers = _auth_headers(credentials)
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(f"{_API}/pages/{item_id}", headers=headers)
            _check(resp, self.app_type)
            page = resp.json()
            item = await self._fetch_page_content(client, headers, page)
            if not item:
                raise ConnectorError(f"Could not parse Notion page {item_id}", connector=self.app_type)
            return item

    # ------------------------------------------------------------------

    async def _fetch_page_content(
        self,
        client: httpx.AsyncClient,
        headers: dict,
        page: dict,
    ) -> ExternalItem | None:
        """Fetch the block tree of *page* and convert it to plain text.

        Args:
            client:  Shared HTTP client.
            headers: Auth headers.
            page:    Notion page object dict.

        Returns:
            :class:`ExternalItem` or *None* if no readable content.
        """
        page_id = page.get("id", "")
        title = _extract_title(page)
        url = page.get("url", f"https://notion.so/{page_id.replace('-', '')}")

        blocks = await _fetch_blocks(client, headers, page_id)
        content = _blocks_to_text(blocks)

        if not content.strip():
            return None

        last_edited = page.get("last_edited_time", "")
        return ExternalItem.build(
            external_id=page_id,
            title=title or "Untitled",
            content=truncate(f"# {title}\n\n{content}"),
            source_url=url,
            metadata={"last_edited": last_edited},
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _auth_headers(credentials: Credentials) -> dict:
    return {
        "Authorization": f"Bearer {credentials.access_token}",
        "Notion-Version": _NOTION_VERSION,
    }


def _check(resp: httpx.Response, connector: str) -> None:
    if resp.status_code == 401:
        raise ConnectorError("Notion token expired or revoked.", connector=connector, status_code=401)
    if resp.status_code not in (200, 201):
        raise ConnectorError(
            f"Notion API error {resp.status_code}: {resp.text}", connector=connector
        )


def _extract_title(page: dict) -> str:
    """Extract the page title from its properties."""
    props = page.get("properties", {})
    for prop in props.values():
        if prop.get("type") == "title":
            parts = prop.get("title", [])
            return "".join(p.get("plain_text", "") for p in parts)
    return "Untitled"


async def _fetch_blocks(
    client: httpx.AsyncClient,
    headers: dict,
    block_id: str,
    depth: int = 0,
) -> list[dict]:
    """Recursively fetch all blocks under *block_id*.

    Args:
        client:   HTTP client.
        headers:  Auth headers.
        block_id: Page or block ID.
        depth:    Current recursion depth (capped at 3 to avoid huge trees).

    Returns:
        Flat list of block dicts with nested ``children`` expanded inline.
    """
    if depth > 3:
        return []

    blocks: list[dict] = []
    cursor: str | None = None

    while True:
        params: dict = {"page_size": 100}
        if cursor:
            params["start_cursor"] = cursor

        resp = await client.get(
            f"https://api.notion.com/v1/blocks/{block_id}/children",
            headers=headers,
            params=params,
        )
        if resp.status_code != 200:
            break

        data = resp.json()
        for block in data.get("results", []):
            blocks.append(block)
            if block.get("has_children"):
                children = await _fetch_blocks(client, headers, block["id"], depth + 1)
                blocks.extend(children)

        if data.get("has_more"):
            cursor = data.get("next_cursor")
        else:
            break

    return blocks


def _rich_text_to_str(rich_texts: list[dict]) -> str:
    """Convert a Notion rich_text array to a plain string."""
    return "".join(rt.get("plain_text", "") for rt in rich_texts)


def _blocks_to_text(blocks: list[dict]) -> str:
    """Convert a list of Notion blocks to plain text.

    Args:
        blocks: List of Notion block dicts.

    Returns:
        Multi-line plain-text string.
    """
    lines: list[str] = []
    for block in blocks:
        btype = block.get("type", "")
        content = block.get(btype, {})

        if btype in ("paragraph", "quote", "callout"):
            text = _rich_text_to_str(content.get("rich_text", []))
            if text.strip():
                lines.append(text)

        elif btype in ("heading_1", "heading_2", "heading_3"):
            level = btype[-1]
            text = _rich_text_to_str(content.get("rich_text", []))
            if text.strip():
                lines.append(f"{'#' * int(level)} {text}")

        elif btype in ("bulleted_list_item", "numbered_list_item", "to_do"):
            text = _rich_text_to_str(content.get("rich_text", []))
            if text.strip():
                lines.append(f"- {text}")

        elif btype == "code":
            text = _rich_text_to_str(content.get("rich_text", []))
            lang = content.get("language", "")
            if text.strip():
                lines.append(f"```{lang}\n{text}\n```")

        elif btype == "divider":
            lines.append("---")

        elif btype == "table_row":
            cells = content.get("cells", [])
            row_text = " | ".join(_rich_text_to_str(cell) for cell in cells)
            if row_text.strip():
                lines.append(row_text)

    return "\n".join(lines)
