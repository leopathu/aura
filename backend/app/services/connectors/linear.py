"""Linear connector — fetches issues and comments via the Linear GraphQL API."""

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

_GRAPHQL_URL = "https://api.linear.app/graphql"

_ISSUES_QUERY = """
query IssueList($first: Int!, $after: String, $filter: IssueFilter) {
  issues(first: $first, after: $after, filter: $filter, orderBy: updatedAt) {
    nodes {
      id
      identifier
      title
      description
      state { name }
      priority
      assignee { displayName }
      team { key name }
      labels { nodes { name } }
      updatedAt
      url
      comments(first: 20) {
        nodes {
          id
          body
          user { displayName }
          createdAt
        }
      }
    }
    pageInfo { hasNextPage endCursor }
  }
}
"""

_SINGLE_ISSUE_QUERY = """
query SingleIssue($id: String!) {
  issue(id: $id) {
    id identifier title description
    state { name }
    priority
    assignee { displayName }
    team { key name }
    labels { nodes { name } }
    updatedAt url
    comments(first: 50) {
      nodes { id body user { displayName } createdAt }
    }
  }
}
"""


class LinearConnector(BaseConnector):
    """Fetches Linear issues and comments via the Linear GraphQL API."""

    app_type = "linear"

    async def list_items(
        self,
        credentials: Credentials,
        config: dict | None = None,
    ) -> list[ExternalItem]:
        """Fetch issues from Linear, optionally filtered by team keys or states.

        Config keys:
        - ``team_keys`` (list[str]): Linear team keys (e.g. ``["ENG", "PRODUCT"]``).
        - ``states`` (list[str]): State names to include (e.g. ``["In Progress", "Done"]``).
        - ``max_issues`` (int): Hard cap (default 500).

        Args:
            credentials: OAuth credentials with ``read`` scope.
            config:      Per-connection filter config.

        Returns:
            List of :class:`ExternalItem` objects.
        """
        cfg = config or {}
        max_issues: int = cfg.get("max_issues", 500)
        team_keys: list[str] = cfg.get("team_keys", [])
        states: list[str] = cfg.get("states", [])

        # Build GraphQL filter.
        gql_filter: dict = {}
        if team_keys:
            gql_filter["team"] = {"key": {"in": team_keys}}
        if states:
            gql_filter["state"] = {"name": {"in": states}}

        headers = _auth_headers(credentials)
        items: list[ExternalItem] = []
        cursor: str | None = None

        async with httpx.AsyncClient(timeout=30) as client:
            while len(items) < max_issues:
                variables: dict = {
                    "first": min(50, max_issues - len(items)),
                    "after": cursor,
                }
                if gql_filter:
                    variables["filter"] = gql_filter

                data = await _gql(client, headers, _ISSUES_QUERY, variables)
                issues_data = data.get("issues", {})

                for node in issues_data.get("nodes", []):
                    items.append(_parse_issue(node))

                page_info = issues_data.get("pageInfo", {})
                if page_info.get("hasNextPage"):
                    cursor = page_info.get("endCursor")
                else:
                    break

        return items

    async def fetch_item(
        self,
        credentials: Credentials,
        item_id: str,
        config: dict | None = None,
    ) -> ExternalItem:
        """Fetch a single Linear issue by its UUID.

        Args:
            credentials: OAuth credentials.
            item_id:     Linear issue UUID.
            config:      Unused.

        Returns:
            The fetched :class:`ExternalItem`.
        """
        headers = _auth_headers(credentials)
        async with httpx.AsyncClient(timeout=30) as client:
            data = await _gql(client, headers, _SINGLE_ISSUE_QUERY, {"id": item_id})
            node = data.get("issue")
            if not node:
                raise ConnectorError(f"Linear issue {item_id} not found.", connector=self.app_type)
            return _parse_issue(node)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _auth_headers(credentials: Credentials) -> dict:
    return {
        "Authorization": f"Bearer {credentials.access_token}",
        "Content-Type": "application/json",
    }


async def _gql(
    client: httpx.AsyncClient,
    headers: dict,
    query: str,
    variables: dict,
) -> dict:
    """Execute a GraphQL query and return the ``data`` portion.

    Args:
        client:    Shared HTTP client.
        headers:   Auth headers.
        query:     GraphQL query string.
        variables: Query variables dict.

    Returns:
        The ``data`` dict from the GraphQL response.

    Raises:
        ConnectorError: On HTTP errors or GraphQL errors.
    """
    resp = await client.post(
        _GRAPHQL_URL,
        headers=headers,
        json={"query": query, "variables": variables},
    )
    if resp.status_code == 401:
        raise ConnectorError("Linear token expired or revoked.", connector="linear", status_code=401)
    if resp.status_code != 200:
        raise ConnectorError(f"Linear API error {resp.status_code}: {resp.text}", connector="linear")

    body = resp.json()
    if "errors" in body:
        msgs = "; ".join(e.get("message", "") for e in body["errors"])
        raise ConnectorError(f"Linear GraphQL errors: {msgs}", connector="linear")

    return body.get("data", {})


def _parse_issue(node: dict) -> ExternalItem:
    """Convert a Linear issue GraphQL node to an :class:`ExternalItem`."""
    issue_id = node.get("id", "")
    identifier = node.get("identifier", issue_id)
    title = node.get("title", "Untitled")
    description = (node.get("description") or "").strip()
    state = (node.get("state") or {}).get("name", "")
    assignee = (node.get("assignee") or {}).get("displayName", "")
    team = (node.get("team") or {}).get("name", "")
    labels = [lbl.get("name", "") for lbl in (node.get("labels") or {}).get("nodes", [])]
    url = node.get("url", f"https://linear.app/issue/{identifier}")

    comment_lines: list[str] = []
    for c in (node.get("comments") or {}).get("nodes", []):
        user = (c.get("user") or {}).get("displayName", "unknown")
        body = (c.get("body") or "").strip()
        if body:
            comment_lines.append(f"{user}: {body}")

    content_parts = [f"Issue {identifier}: {title}"]
    if description:
        content_parts.append(f"Description:\n{description}")
    if comment_lines:
        content_parts.append("Comments:\n" + "\n\n".join(comment_lines))

    return ExternalItem.build(
        external_id=issue_id,
        title=f"{identifier}: {title}",
        content=truncate("\n\n".join(content_parts)),
        source_url=url,
        metadata={
            "identifier": identifier,
            "state": state,
            "assignee": assignee,
            "team": team,
            "labels": labels,
            "updated_at": node.get("updatedAt", ""),
        },
    )
