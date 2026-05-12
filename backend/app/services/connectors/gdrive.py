"""Google Drive connector — fetches Docs, Sheets, and PDFs as plain text."""

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

_API = "https://www.googleapis.com/drive/v3"
_EXPORT_API = "https://www.googleapis.com/drive/v3/files/{id}/export"
_DOWNLOAD_API = "https://www.googleapis.com/drive/v3/files/{id}?alt=media"

# MIME types we can handle — mapped to the export format we request.
_EXPORTABLE: dict[str, str] = {
    "application/vnd.google-apps.document": "text/plain",
    "application/vnd.google-apps.spreadsheet": "text/csv",
    "application/vnd.google-apps.presentation": "text/plain",
}
_DOWNLOADABLE: set[str] = {
    "application/pdf",
    "text/plain",
    "text/markdown",
    "text/html",
}
# Page size for list calls
_PAGE_SIZE = 100


class GDriveConnector(BaseConnector):
    """Fetches readable files from Google Drive via the Drive REST API v3."""

    app_type = "gdrive"

    async def list_items(
        self,
        credentials: Credentials,
        config: dict | None = None,
    ) -> list[ExternalItem]:
        """List all readable files from the user's Google Drive.

        Respects optional config keys:
        - ``folder_ids`` (list[str]): limit to specific folder IDs.
        - ``max_files`` (int): hard cap on total files returned (default 500).

        Args:
            credentials: OAuth credentials with Drive read scope.
            config:      Per-connection filter config.

        Returns:
            List of :class:`ExternalItem` objects.
        """
        cfg = config or {}
        max_files: int = cfg.get("max_files", 500)
        folder_ids: list[str] = cfg.get("folder_ids", [])

        # Build the MIME-type query filter.
        mime_filter = " or ".join(
            f"mimeType='{m}'" for m in list(_EXPORTABLE) + list(_DOWNLOADABLE)
        )
        query = f"trashed=false and ({mime_filter})"

        if folder_ids:
            parent_filter = " or ".join(f"'{fid}' in parents" for fid in folder_ids)
            query += f" and ({parent_filter})"

        headers = {"Authorization": f"Bearer {credentials.access_token}"}
        items: list[ExternalItem] = []
        page_token: str | None = None

        async with httpx.AsyncClient(timeout=30) as client:
            while len(items) < max_files:
                params: dict = {
                    "q": query,
                    "pageSize": min(_PAGE_SIZE, max_files - len(items)),
                    "fields": "nextPageToken,files(id,name,mimeType,webViewLink,modifiedTime,owners)",
                }
                if page_token:
                    params["pageToken"] = page_token

                resp = await client.get(f"{_API}/files", headers=headers, params=params)
                if resp.status_code == 401:
                    raise ConnectorError("Google Drive token expired or revoked.", connector=self.app_type, status_code=401)
                if resp.status_code != 200:
                    raise ConnectorError(f"Drive list error {resp.status_code}: {resp.text}", connector=self.app_type)

                data = resp.json()
                for file in data.get("files", []):
                    try:
                        item = await self._fetch_file(client, headers, file)
                        if item:
                            items.append(item)
                    except Exception as exc:
                        log.warning("GDrive: skipping file %s — %s", file.get("id"), exc)

                page_token = data.get("nextPageToken")
                if not page_token:
                    break

        return items

    async def fetch_item(
        self,
        credentials: Credentials,
        item_id: str,
        config: dict | None = None,
    ) -> ExternalItem:
        """Fetch a single Drive file by its ID.

        Args:
            credentials: OAuth credentials.
            item_id:     Google Drive file ID.
            config:      Unused for single-file fetch.

        Returns:
            The fetched :class:`ExternalItem`.
        """
        headers = {"Authorization": f"Bearer {credentials.access_token}"}
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{_API}/files/{item_id}",
                headers=headers,
                params={"fields": "id,name,mimeType,webViewLink,modifiedTime,owners"},
            )
            if resp.status_code != 200:
                raise ConnectorError(f"Drive fetch error {resp.status_code}: {resp.text}", connector=self.app_type)

            file = resp.json()
            item = await self._fetch_file(client, headers, file)
            if not item:
                raise ConnectorError(f"Cannot extract text from file {item_id}", connector=self.app_type)
            return item

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _fetch_file(
        self,
        client: httpx.AsyncClient,
        headers: dict,
        file: dict,
    ) -> ExternalItem | None:
        """Download or export a Drive file and return an ExternalItem.

        Args:
            client:  Shared httpx client.
            headers: Auth headers.
            file:    File metadata dict from the Drive list response.

        Returns:
            :class:`ExternalItem` or *None* if content cannot be extracted.
        """
        mime = file.get("mimeType", "")
        file_id = file["id"]
        name = file.get("name", "Untitled")
        url = file.get("webViewLink", f"https://drive.google.com/file/d/{file_id}")
        owner = (file.get("owners") or [{}])[0].get("displayName", "")

        content: str | None = None

        if mime in _EXPORTABLE:
            export_mime = _EXPORTABLE[mime]
            resp = await client.get(
                _EXPORT_API.format(id=file_id),
                headers=headers,
                params={"mimeType": export_mime},
            )
            if resp.status_code == 200:
                content = resp.text
        elif mime in _DOWNLOADABLE:
            resp = await client.get(_DOWNLOAD_API.format(id=file_id), headers=headers)
            if resp.status_code == 200:
                if "html" in mime:
                    content = html_to_text(resp.text)
                elif mime == "application/pdf":
                    content = _extract_pdf_text(resp.content)
                else:
                    content = resp.text

        if not content or not content.strip():
            return None

        return ExternalItem.build(
            external_id=file_id,
            title=name,
            content=truncate(content.strip()),
            source_url=url,
            metadata={
                "mime_type": mime,
                "owner": owner,
                "modified_at": file.get("modifiedTime", ""),
            },
        )


def _extract_pdf_text(data: bytes) -> str:
    """Extract plain text from PDF bytes using pypdf.

    Args:
        data: Raw PDF bytes.

    Returns:
        Extracted plain text, or empty string on failure.
    """
    try:
        import io

        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(data))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as exc:
        log.warning("PDF extraction failed: %s", exc)
        return ""
