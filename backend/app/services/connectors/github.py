"""GitHub connector — fetches issues, PRs, and READMEs via the GitHub REST API."""

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

_API = "https://api.github.com"
_PAGE_SIZE = 50


class GitHubConnector(BaseConnector):
    """Fetches issues, pull requests, and READMEs from GitHub repositories."""

    app_type = "github"

    async def list_items(
        self,
        credentials: Credentials,
        config: dict | None = None,
    ) -> list[ExternalItem]:
        """Fetch issues, PRs, and READMEs from the configured repositories.

        Config keys:
        - ``repos`` (list[str]): Repos in ``owner/repo`` format (required).
        - ``include_prs`` (bool): Fetch pull requests too (default ``true``).
        - ``include_readmes`` (bool): Fetch README (default ``true``).
        - ``state`` (str): Issue state filter — ``"open"``, ``"closed"``, or
          ``"all"`` (default ``"all"``).
        - ``max_issues_per_repo`` (int): Cap (default 500).

        Args:
            credentials: OAuth credentials with ``repo`` scope.
            config:      Per-connection filter config.

        Returns:
            List of :class:`ExternalItem` objects.
        """
        cfg = config or {}
        repos: list[str] = cfg.get("repos", [])
        include_prs: bool = cfg.get("include_prs", True)
        include_readmes: bool = cfg.get("include_readmes", True)
        state: str = cfg.get("state", "all")
        max_per_repo: int = cfg.get("max_issues_per_repo", 500)

        if not repos:
            log.warning("GitHub connector: no repos configured — skipping.")
            return []

        headers = _auth_headers(credentials)
        items: list[ExternalItem] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for repo in repos:
                try:
                    if include_readmes:
                        readme = await self._fetch_readme(client, headers, repo)
                        if readme:
                            items.append(readme)

                    issues = await self._fetch_issues(
                        client, headers, repo,
                        state=state,
                        include_prs=include_prs,
                        max_count=max_per_repo,
                    )
                    items.extend(issues)
                except ConnectorError:
                    raise
                except Exception as exc:
                    log.warning("GitHub: error fetching repo %s — %s", repo, exc)

        return items

    async def fetch_item(
        self,
        credentials: Credentials,
        item_id: str,
        config: dict | None = None,
    ) -> ExternalItem:
        """Fetch a single issue or README.

        *item_id* format:
        - Issues/PRs: ``owner/repo#123``
        - README:     ``owner/repo:readme``

        Args:
            credentials: OAuth credentials.
            item_id:     Composite item ID.
            config:      Unused.

        Returns:
            The fetched :class:`ExternalItem`.
        """
        headers = _auth_headers(credentials)
        async with httpx.AsyncClient(timeout=30) as client:
            if item_id.endswith(":readme"):
                repo = item_id[: -len(":readme")]
                item = await self._fetch_readme(client, headers, repo)
                if not item:
                    raise ConnectorError(f"README not found for {repo}", connector=self.app_type)
                return item

            if "#" in item_id:
                repo, num_str = item_id.rsplit("#", 1)
                resp = await client.get(
                    f"{_API}/repos/{repo}/issues/{num_str}",
                    headers=headers,
                )
                _check(resp, self.app_type)
                return _parse_issue(resp.json(), repo)

            raise ConnectorError(f"Unrecognised GitHub item_id format: {item_id}", connector=self.app_type)

    # ------------------------------------------------------------------

    async def _fetch_readme(
        self,
        client: httpx.AsyncClient,
        headers: dict,
        repo: str,
    ) -> ExternalItem | None:
        resp = await client.get(
            f"{_API}/repos/{repo}/readme",
            headers={**headers, "Accept": "application/vnd.github.raw"},
        )
        if resp.status_code == 404:
            return None
        _check(resp, self.app_type)

        content = resp.text
        if not content.strip():
            return None

        return ExternalItem.build(
            external_id=f"{repo}:readme",
            title=f"{repo} README",
            content=truncate(content),
            source_url=f"https://github.com/{repo}#readme",
            metadata={"repo": repo, "type": "readme"},
        )

    async def _fetch_issues(
        self,
        client: httpx.AsyncClient,
        headers: dict,
        repo: str,
        state: str,
        include_prs: bool,
        max_count: int,
    ) -> list[ExternalItem]:
        items: list[ExternalItem] = []
        page = 1

        while len(items) < max_count:
            resp = await client.get(
                f"{_API}/repos/{repo}/issues",
                headers=headers,
                params={
                    "state": state,
                    "per_page": min(_PAGE_SIZE, max_count - len(items)),
                    "page": page,
                },
            )
            if resp.status_code == 404:
                break
            _check(resp, self.app_type)
            issues = resp.json()
            if not issues:
                break

            for issue in issues:
                is_pr = "pull_request" in issue
                if is_pr and not include_prs:
                    continue
                # Fetch comments separately for richer content.
                comments_text = await self._fetch_issue_comments(
                    client, headers, repo, issue["number"]
                )
                items.append(_parse_issue(issue, repo, comments_text))

            page += 1

        return items

    async def _fetch_issue_comments(
        self,
        client: httpx.AsyncClient,
        headers: dict,
        repo: str,
        issue_number: int,
    ) -> str:
        resp = await client.get(
            f"{_API}/repos/{repo}/issues/{issue_number}/comments",
            headers=headers,
            params={"per_page": 50},
        )
        if resp.status_code != 200:
            return ""
        lines: list[str] = []
        for c in resp.json():
            user = (c.get("user") or {}).get("login", "unknown")
            body = (c.get("body") or "").strip()
            if body:
                lines.append(f"{user}: {body}")
        return "\n\n".join(lines)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _auth_headers(credentials: Credentials) -> dict:
    return {
        "Authorization": f"Bearer {credentials.access_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _check(resp: httpx.Response, connector: str) -> None:
    if resp.status_code == 401:
        raise ConnectorError("GitHub token expired or revoked.", connector=connector, status_code=401)
    if resp.status_code not in (200, 201):
        raise ConnectorError(
            f"GitHub API error {resp.status_code}: {resp.text}", connector=connector
        )


def _parse_issue(issue: dict, repo: str, comments_text: str = "") -> ExternalItem:
    """Convert a GitHub issue/PR dict to an :class:`ExternalItem`."""
    number = issue["number"]
    title = issue.get("title", f"Issue #{number}")
    body = (issue.get("body") or "").strip()
    is_pr = "pull_request" in issue
    doc_type = "Pull Request" if is_pr else "Issue"

    content_parts = [f"{doc_type} #{number}: {title}"]
    if body:
        content_parts.append(f"Description:\n{body}")
    if comments_text:
        content_parts.append(f"Comments:\n{comments_text}")

    content = "\n\n".join(content_parts)
    url = issue.get("html_url", f"https://github.com/{repo}/issues/{number}")
    state = issue.get("state", "")
    user = (issue.get("user") or {}).get("login", "")
    labels = [lbl.get("name", "") for lbl in issue.get("labels", [])]

    return ExternalItem.build(
        external_id=f"{repo}#{number}",
        title=f"{repo} {doc_type} #{number}: {title}",
        content=truncate(content),
        source_url=url,
        metadata={"repo": repo, "type": doc_type.lower().replace(" ", "_"),
                  "state": state, "author": user, "labels": labels,
                  "updated_at": issue.get("updated_at", "")},
    )
