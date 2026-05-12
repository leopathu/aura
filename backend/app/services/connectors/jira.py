"""Jira connector — fetches issues and comments via the Jira REST API v3."""

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
_FIELDS = "summary,description,status,priority,assignee,reporter,labels,created,updated,comment"


class JiraConnector(BaseConnector):
    """Fetches Jira issues and their comments via the REST API v3."""

    app_type = "jira"

    async def list_items(
        self,
        credentials: Credentials,
        config: dict | None = None,
    ) -> list[ExternalItem]:
        """List issues from one or more Jira projects.

        Config keys:
        - ``project_keys`` (list[str]): Project keys to sync (e.g. ``["PROJ", "ENG"]``).
          Required — without this the connector returns an empty list.
        - ``max_issues`` (int): Hard cap (default 1000).
        - ``jql_extra`` (str): Additional JQL appended with ``AND``.

        Args:
            credentials: OAuth credentials (extra[``cloud_id``] required).
            config:      Per-connection filter config.

        Returns:
            List of :class:`ExternalItem` objects, one per Jira issue.
        """
        cfg = config or {}
        project_keys: list[str] = cfg.get("project_keys", [])
        max_issues: int = cfg.get("max_issues", 1000)
        jql_extra: str = cfg.get("jql_extra", "")

        if not project_keys:
            log.warning("Jira connector: no project_keys configured — skipping.")
            return []

        cloud_id = credentials.extra.get("cloud_id", "")
        if not cloud_id:
            raise ConnectorError(
                "Jira cloud_id missing from credentials. Re-authorise the connection.",
                connector=self.app_type,
            )

        base_url = f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3"
        project_filter = " OR ".join(f"project = {k}" for k in project_keys)
        jql = f"({project_filter}) ORDER BY updated DESC"
        if jql_extra:
            jql = f"({project_filter}) AND ({jql_extra}) ORDER BY updated DESC"

        headers = _auth_headers(credentials)
        items: list[ExternalItem] = []
        start_at = 0

        async with httpx.AsyncClient(timeout=30) as client:
            while len(items) < max_issues:
                resp = await client.get(
                    f"{base_url}/search",
                    headers=headers,
                    params={
                        "jql": jql,
                        "startAt": start_at,
                        "maxResults": min(_PAGE_SIZE, max_issues - len(items)),
                        "fields": _FIELDS,
                    },
                )
                _check(resp, self.app_type)
                data = resp.json()

                for issue in data.get("issues", []):
                    item = _parse_issue(issue, cloud_id)
                    if item:
                        items.append(item)

                total = data.get("total", 0)
                start_at += len(data.get("issues", []))
                if start_at >= total:
                    break

        return items

    async def fetch_item(
        self,
        credentials: Credentials,
        item_id: str,
        config: dict | None = None,
    ) -> ExternalItem:
        """Fetch a single Jira issue by its key (e.g. ``PROJ-123``).

        Args:
            credentials: OAuth credentials.
            item_id:     Jira issue key.
            config:      Unused.

        Returns:
            The fetched :class:`ExternalItem`.
        """
        cloud_id = credentials.extra.get("cloud_id", "")
        if not cloud_id:
            raise ConnectorError("Jira cloud_id missing.", connector=self.app_type)

        base_url = f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3"
        headers = _auth_headers(credentials)

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{base_url}/issue/{item_id}",
                headers=headers,
                params={"fields": _FIELDS},
            )
            _check(resp, self.app_type)
            issue = resp.json()
            item = _parse_issue(issue, cloud_id)
            if not item:
                raise ConnectorError(f"Could not parse issue {item_id}", connector=self.app_type)
            return item


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
        raise ConnectorError("Jira token expired or revoked.", connector=connector, status_code=401)
    if resp.status_code not in (200, 201):
        raise ConnectorError(
            f"Jira API error {resp.status_code}: {resp.text}", connector=connector
        )


def _adf_to_text(node: dict | None) -> str:
    """Convert Atlassian Document Format (ADF) JSON to plain text.

    Args:
        node: ADF document node dict (or None).

    Returns:
        Plain-text string.
    """
    if not node:
        return ""
    if isinstance(node, str):
        return node

    node_type = node.get("type", "")
    text_parts: list[str] = []

    if node_type == "text":
        return node.get("text", "")

    for child in node.get("content", []):
        text_parts.append(_adf_to_text(child))

    separator = "\n" if node_type in ("paragraph", "heading", "listItem", "blockquote", "codeBlock") else " "
    return separator.join(p for p in text_parts if p)


def _parse_issue(issue: dict, cloud_id: str) -> ExternalItem | None:
    """Convert a Jira issue dict to an :class:`ExternalItem`.

    Args:
        issue:    Raw Jira issue dict from the REST API.
        cloud_id: Atlassian cloud site ID for building the source URL.

    Returns:
        :class:`ExternalItem` or *None* if the issue has no usable content.
    """
    key = issue.get("key", "")
    fields = issue.get("fields", {})

    summary = fields.get("summary") or key
    description_adf = fields.get("description")
    description = _adf_to_text(description_adf) if isinstance(description_adf, dict) else (description_adf or "")

    # Collect comments.
    comment_texts: list[str] = []
    comments = (fields.get("comment") or {}).get("comments", [])
    for c in comments:
        author = (c.get("author") or {}).get("displayName", "unknown")
        body_adf = c.get("body")
        body = _adf_to_text(body_adf) if isinstance(body_adf, dict) else (body_adf or "")
        if body.strip():
            comment_texts.append(f"{author}: {body.strip()}")

    content_parts = [f"Issue: {key}\nSummary: {summary}"]
    if description.strip():
        content_parts.append(f"Description:\n{description.strip()}")
    if comment_texts:
        content_parts.append("Comments:\n" + "\n\n".join(comment_texts))

    content = "\n\n".join(content_parts)
    if not content.strip():
        return None

    status = (fields.get("status") or {}).get("name", "")
    priority = (fields.get("priority") or {}).get("name", "")
    assignee = (fields.get("assignee") or {}).get("displayName", "")
    reporter = (fields.get("reporter") or {}).get("displayName", "")
    labels = fields.get("labels", [])
    source_url = f"https://{cloud_id}.atlassian.net/browse/{key}"

    return ExternalItem.build(
        external_id=key,
        title=f"{key}: {summary}",
        content=truncate(content),
        source_url=source_url,
        metadata={
            "status": status,
            "priority": priority,
            "assignee": assignee,
            "reporter": reporter,
            "labels": labels,
            "updated_at": fields.get("updated", ""),
        },
    )
