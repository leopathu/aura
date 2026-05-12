"""Connector registry — maps app_type strings to BaseConnector implementations."""

from __future__ import annotations

from app.services.connectors.base import BaseConnector, ConnectorError, ExternalItem
from app.services.connectors.confluence import ConfluenceConnector
from app.services.connectors.gdrive import GDriveConnector
from app.services.connectors.github import GitHubConnector
from app.services.connectors.gmail import GmailConnector
from app.services.connectors.jira import JiraConnector
from app.services.connectors.linear import LinearConnector
from app.services.connectors.notion import NotionConnector
from app.services.connectors.slack import SlackConnector

__all__ = [
    "CONNECTORS",
    "get_connector",
    "BaseConnector",
    "ConnectorError",
    "ExternalItem",
]

CONNECTORS: dict[str, type[BaseConnector]] = {
    "gdrive": GDriveConnector,
    "gmail": GmailConnector,
    "slack": SlackConnector,
    "jira": JiraConnector,
    "confluence": ConfluenceConnector,
    "notion": NotionConnector,
    "github": GitHubConnector,
    "linear": LinearConnector,
}


def get_connector(app_type: str) -> BaseConnector:
    """Return an instantiated connector for the given *app_type*.

    Args:
        app_type: One of the keys in :data:`CONNECTORS`.

    Returns:
        A fresh :class:`BaseConnector` instance.

    Raises:
        KeyError: If *app_type* is not registered.
    """
    try:
        return CONNECTORS[app_type]()
    except KeyError:
        supported = list(CONNECTORS)
        raise KeyError(f"Unknown app_type '{app_type}'. Supported: {supported}") from None
