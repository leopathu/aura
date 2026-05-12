"""Slack connector — fetches messages and threads from selected channels."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx

from app.services.connectors.base import (
    BaseConnector,
    ConnectorError,
    ExternalItem,
    truncate,
)
from app.services.oauth.base import Credentials

log = logging.getLogger(__name__)

_API = "https://slack.com/api"
_PAGE_SIZE = 100
# Group messages into daily bundles so each ExternalItem covers one channel-day.
_BUNDLE_DAYS = 1


class SlackConnector(BaseConnector):
    """Fetches message history from Slack channels via the Web API."""

    app_type = "slack"

    async def list_items(
        self,
        credentials: Credentials,
        config: dict | None = None,
    ) -> list[ExternalItem]:
        """Fetch recent messages from the configured channels.

        Config keys:
        - ``channel_ids`` (list[str]): Specific channel IDs to sync.
          If omitted, all joined public channels are synced.
        - ``max_days`` (int): How many days of history to fetch (default 30).
        - ``max_messages_per_channel`` (int): Cap per channel (default 500).

        Each channel's messages are grouped into daily bundles, yielding one
        :class:`ExternalItem` per channel per day.

        Args:
            credentials: OAuth credentials with ``channels:history`` scope.
            config:      Per-connection filter config.

        Returns:
            List of :class:`ExternalItem` objects.
        """
        cfg = config or {}
        max_days: int = cfg.get("max_days", 30)
        max_msgs: int = cfg.get("max_messages_per_channel", 500)
        channel_ids: list[str] = cfg.get("channel_ids", [])

        headers = _auth_headers(credentials)

        async with httpx.AsyncClient(timeout=30) as client:
            if not channel_ids:
                channel_ids = await _list_joined_channels(client, headers)

            oldest = str(
                datetime.now(timezone.utc).timestamp() - max_days * 86400
            )

            items: list[ExternalItem] = []
            for channel_id in channel_ids:
                channel_name = await _get_channel_name(client, headers, channel_id)
                try:
                    channel_items = await self._fetch_channel(
                        client, headers, channel_id, channel_name, oldest, max_msgs
                    )
                    items.extend(channel_items)
                except Exception as exc:
                    log.warning("Slack: skipping channel %s — %s", channel_id, exc)

        return items

    async def fetch_item(
        self,
        credentials: Credentials,
        item_id: str,
        config: dict | None = None,
    ) -> ExternalItem:
        """Fetch a single channel-day bundle.

        *item_id* must be in the format ``{channel_id}:{date}`` (e.g.
        ``C012AB3CD:2026-05-01``).

        Args:
            credentials: OAuth credentials.
            item_id:     ``channel_id:date`` composite key.
            config:      Unused.

        Returns:
            The fetched :class:`ExternalItem`.
        """
        parts = item_id.split(":", 1)
        if len(parts) != 2:
            raise ConnectorError(
                f"Invalid Slack item_id format: '{item_id}'. Expected 'channel_id:date'.",
                connector=self.app_type,
            )
        channel_id, date_str = parts
        headers = _auth_headers(credentials)

        async with httpx.AsyncClient(timeout=30) as client:
            channel_name = await _get_channel_name(client, headers, channel_id)
            # Fetch a narrow window: midnight → midnight of the given date.
            try:
                day_ts = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp()
            except ValueError as exc:
                raise ConnectorError(f"Invalid date in item_id: {date_str}", connector=self.app_type) from exc

            items = await self._fetch_channel(
                client, headers, channel_id, channel_name,
                oldest=str(day_ts), max_msgs=500, latest=str(day_ts + 86400)
            )
            if not items:
                raise ConnectorError(f"No messages found for {item_id}", connector=self.app_type)
            return items[0]

    # ------------------------------------------------------------------

    async def _fetch_channel(
        self,
        client: httpx.AsyncClient,
        headers: dict,
        channel_id: str,
        channel_name: str,
        oldest: str,
        max_msgs: int,
        latest: str | None = None,
    ) -> list[ExternalItem]:
        """Fetch all messages in *channel_id* since *oldest* and bundle by day.

        Args:
            client:       Shared HTTP client.
            headers:      Auth headers.
            channel_id:   Slack channel ID.
            channel_name: Human-readable channel name.
            oldest:       Unix timestamp string — fetch messages after this.
            max_msgs:     Maximum number of messages to retrieve.
            latest:       Optional upper-bound timestamp.

        Returns:
            List of :class:`ExternalItem` objects (one per calendar day).
        """
        messages: list[dict] = []
        cursor: str | None = None

        while len(messages) < max_msgs:
            params: dict = {
                "channel": channel_id,
                "limit": min(_PAGE_SIZE, max_msgs - len(messages)),
                "oldest": oldest,
            }
            if latest:
                params["latest"] = latest
            if cursor:
                params["cursor"] = cursor

            resp = await client.get(f"{_API}/conversations.history", headers=headers, params=params)
            data = resp.json()
            _check_slack(data, self.app_type)

            messages.extend(data.get("messages", []))
            meta = data.get("response_metadata", {})
            cursor = meta.get("next_cursor") or None
            if not cursor:
                break

        # Resolve user names for all messages.
        user_ids = {m["user"] for m in messages if "user" in m}
        user_names = await _resolve_users(client, headers, user_ids)

        return _bundle_by_day(messages, user_names, channel_id, channel_name)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _auth_headers(credentials: Credentials) -> dict:
    return {"Authorization": f"Bearer {credentials.access_token}"}


def _check_slack(data: dict, connector: str) -> None:
    if not data.get("ok"):
        error = data.get("error", "unknown")
        if error in {"invalid_auth", "token_revoked", "not_authed"}:
            raise ConnectorError(f"Slack auth error: {error}", connector=connector, status_code=401)
        raise ConnectorError(f"Slack API error: {error}", connector=connector)


async def _list_joined_channels(client: httpx.AsyncClient, headers: dict) -> list[str]:
    """Return IDs of all channels the bot/user has joined."""
    ids: list[str] = []
    cursor: str | None = None
    while True:
        params: dict = {"types": "public_channel,private_channel", "limit": 200}
        if cursor:
            params["cursor"] = cursor
        resp = await client.get(f"{_API}/conversations.list", headers=headers, params=params)
        data = resp.json()
        _check_slack(data, "slack")
        for ch in data.get("channels", []):
            if ch.get("is_member"):
                ids.append(ch["id"])
        cursor = (data.get("response_metadata") or {}).get("next_cursor") or None
        if not cursor:
            break
    return ids


async def _get_channel_name(
    client: httpx.AsyncClient, headers: dict, channel_id: str
) -> str:
    """Resolve a channel ID to its display name."""
    resp = await client.get(
        f"{_API}/conversations.info",
        headers=headers,
        params={"channel": channel_id},
    )
    data = resp.json()
    if data.get("ok"):
        return data.get("channel", {}).get("name", channel_id)
    return channel_id


async def _resolve_users(
    client: httpx.AsyncClient, headers: dict, user_ids: set[str]
) -> dict[str, str]:
    """Batch-resolve user IDs to display names."""
    names: dict[str, str] = {}
    for uid in user_ids:
        try:
            resp = await client.get(
                f"{_API}/users.info", headers=headers, params={"user": uid}
            )
            data = resp.json()
            if data.get("ok"):
                names[uid] = data["user"].get("real_name") or data["user"].get("name", uid)
            else:
                names[uid] = uid
        except Exception:
            names[uid] = uid
    return names


def _bundle_by_day(
    messages: list[dict],
    user_names: dict[str, str],
    channel_id: str,
    channel_name: str,
) -> list[ExternalItem]:
    """Group messages into per-day bundles and return as ExternalItems.

    Args:
        messages:     Raw Slack message dicts (newest-first from API).
        user_names:   Map of user_id → display name.
        channel_id:   Slack channel ID.
        channel_name: Human-readable channel name.

    Returns:
        List of :class:`ExternalItem` objects, one per calendar day.
    """
    from collections import defaultdict

    # Group by YYYY-MM-DD date string.
    daily: dict[str, list[dict]] = defaultdict(list)
    for msg in messages:
        try:
            ts = float(msg.get("ts", 0))
            date_str = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
            daily[date_str].append(msg)
        except Exception:
            continue

    items: list[ExternalItem] = []
    for date_str, day_msgs in sorted(daily.items()):
        lines: list[str] = [f"# #{channel_name} — {date_str}\n"]
        for msg in reversed(day_msgs):  # chronological order
            user = user_names.get(msg.get("user", ""), msg.get("user", "unknown"))
            text = msg.get("text", "").strip()
            if not text:
                continue
            ts = msg.get("ts", "")
            try:
                time_str = datetime.fromtimestamp(float(ts), tz=timezone.utc).strftime("%H:%M")
            except Exception:
                time_str = ""
            lines.append(f"[{time_str}] {user}: {text}")

        content = "\n".join(lines)
        if len(content) < 20:
            continue

        items.append(
            ExternalItem.build(
                external_id=f"{channel_id}:{date_str}",
                title=f"#{channel_name} — {date_str}",
                content=truncate(content),
                source_url=f"https://slack.com/app_redirect?channel={channel_id}",
                metadata={"channel_id": channel_id, "channel_name": channel_name, "date": date_str},
            )
        )
    return items
