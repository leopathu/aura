"""Base connector interface and shared data types for all app connectors."""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator

from app.services.oauth.base import Credentials


@dataclass
class ExternalItem:
    """A single normalised document fetched from an external app.

    Attributes:
        external_id:  Stable unique identifier in the source app (e.g. file ID,
                      issue key, message timestamp).
        title:        Human-readable title (filename, issue summary, channel+date, …).
        content:      Full plain-text body, ready for chunking and embedding.
        source_url:   Deep-link back to the original item in the external app.
        content_hash: SHA-256 hex digest of *content* — used for change detection.
        metadata:     Arbitrary extra fields (author, labels, modified_at, …).
                      Must be JSON-serialisable.
    """

    external_id: str
    title: str
    content: str
    source_url: str
    content_hash: str = field(init=False)
    metadata: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.content_hash = _sha256(self.content)

    @classmethod
    def build(
        cls,
        external_id: str,
        title: str,
        content: str,
        source_url: str,
        metadata: dict | None = None,
    ) -> "ExternalItem":
        """Convenience constructor — computes *content_hash* automatically.

        Args:
            external_id: Stable ID in the source app.
            title:       Document title.
            content:     Plain-text body.
            source_url:  Deep-link URL.
            metadata:    Optional extra fields dict.

        Returns:
            Fully populated :class:`ExternalItem`.
        """
        return cls(
            external_id=external_id,
            title=title,
            content=content,
            source_url=source_url,
            metadata=metadata or {},
        )


class ConnectorError(Exception):
    """Raised when a connector cannot fetch or parse data from the external app."""

    def __init__(self, message: str, connector: str = "", status_code: int | None = None) -> None:
        self.connector = connector
        self.status_code = status_code
        super().__init__(message)


class BaseConnector(ABC):
    """Abstract connector that turns an external app's data into :class:`ExternalItem` objects.

    Each connector is stateless — credentials and optional ``config`` (the
    ``agent_connections.config_json`` dict) are passed into every call so the
    same instance can serve multiple connections concurrently.
    """

    # Subclasses must set this to the matching ``app_type`` slug.
    app_type: str = ""

    @abstractmethod
    async def list_items(
        self,
        credentials: Credentials,
        config: dict | None = None,
    ) -> list[ExternalItem]:
        """Fetch all syncable items from the external app.

        The connector is responsible for pagination — it must not return until
        **all** pages have been fetched.

        Args:
            credentials: Decrypted OAuth token set for this connection.
            config:      Optional per-connection filter config from
                         ``agent_connections.config_json``.

        Returns:
            List of :class:`ExternalItem` objects, one per syncable document.

        Raises:
            ConnectorError: On API errors, auth failures, or parse failures.
        """

    @abstractmethod
    async def fetch_item(
        self,
        credentials: Credentials,
        item_id: str,
        config: dict | None = None,
    ) -> ExternalItem:
        """Fetch a single item by its *item_id*.

        Used for incremental refresh of a specific document.

        Args:
            credentials: Decrypted OAuth token set.
            item_id:     The ``external_id`` of the item to fetch.
            config:      Optional per-connection filter config.

        Returns:
            A fresh :class:`ExternalItem`.

        Raises:
            ConnectorError: If the item is not found or the API call fails.
        """

    async def iter_items(
        self,
        credentials: Credentials,
        config: dict | None = None,
    ) -> AsyncIterator[ExternalItem]:
        """Async-iterator variant of :meth:`list_items` for large result sets.

        The default implementation simply yields all items from :meth:`list_items`.
        Connectors that support true server-side pagination can override this.

        Args:
            credentials: Decrypted OAuth token set.
            config:      Optional per-connection filter config.

        Yields:
            :class:`ExternalItem` objects one by one.
        """
        for item in await self.list_items(credentials, config):
            yield item


# ---------------------------------------------------------------------------
# Shared text-processing helpers used by multiple connectors
# ---------------------------------------------------------------------------


def _sha256(text: str) -> str:
    """Return the SHA-256 hex digest of *text* (UTF-8 encoded).

    Args:
        text: Input string.

    Returns:
        64-character lowercase hex string.
    """
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def html_to_text(html: str) -> str:
    """Strip HTML tags and return plain text.

    Falls back to raw *html* if *beautifulsoup4* is not installed.

    Args:
        html: Raw HTML string.

    Returns:
        Plain-text string with excess whitespace collapsed.
    """
    try:
        from bs4 import BeautifulSoup  # type: ignore[import-untyped]

        soup = BeautifulSoup(html, "html.parser")
        return " ".join(soup.get_text(separator=" ").split())
    except ImportError:
        import re

        text = re.sub(r"<[^>]+>", " ", html)
        return " ".join(text.split())


def truncate(text: str, max_chars: int = 100_000) -> str:
    """Truncate *text* to *max_chars* characters, appending an ellipsis if cut.

    Args:
        text:      Input string.
        max_chars: Maximum character count (default 100 000).

    Returns:
        Possibly-truncated string.
    """
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n[content truncated]"
