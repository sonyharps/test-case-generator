"""Google Drive upload service (Shared Drive).

Auth resolves in this order via google.auth.default():
- GOOGLE_APPLICATION_CREDENTIALS env (key file) — local dev
- attached VM service account (metadata server) — production

Note: the Drive scope must be requested explicitly — it is NOT covered by
the usual cloud-platform scope. On GCE the instance needs
`https://www.googleapis.com/auth/drive` in its access scopes.
"""
import json
from typing import Optional

import httpx
from google.auth import default as default_credentials
from google.auth.credentials import Credentials
from google.auth.transport.requests import Request as RefreshRequest

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

DRIVE_SCOPE = "https://www.googleapis.com/auth/drive"
XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

_creds: Optional[Credentials] = None
_folder_cache: dict = {}


def _get_credentials() -> Credentials:
    global _creds
    if _creds is None or not _creds.valid:
        _creds, _ = default_credentials(scopes=[DRIVE_SCOPE])
        _creds.refresh(RefreshRequest())
    return _creds


def drive_enabled() -> bool:
    return bool(getattr(settings, "DRIVE_FOLDER_ID", None))


def ensure_subfolder(name: str, parent_folder_id: Optional[str] = None) -> str:
    """Return the Drive folder id for `name` under the configured root folder
    (or a given parent), creating the folder when missing. Cached in-memory
    per (parent, name) so nested paths like Squad/Project stay cheap.
    """
    if not drive_enabled():
        raise RuntimeError("DRIVE_FOLDER_ID is not configured")

    parent = parent_folder_id or settings.DRIVE_FOLDER_ID
    key = f"{parent}:{name.lower()}"
    if key in _folder_cache:
        return _folder_cache[key]

    token = _get_credentials().token
    headers = {"Authorization": f"Bearer {token}"}

    res = httpx.get(
        "https://www.googleapis.com/drive/v3/files",
        params={
            "q": (
                f"'{parent}' in parents "
                f"and name = '{name}' "
                "and mimeType = 'application/vnd.google-apps.folder' "
                "and trashed = false"
            ),
            "fields": "files(id,name)",
            "supportsAllDrives": "true",
            "includeItemsFromAllDrives": "true",
        },
        headers=headers,
        timeout=60,
    )
    res.raise_for_status()
    matches = res.json().get("files", [])

    if matches:
        folder_id = matches[0]["id"]
    else:
        res = httpx.post(
            "https://www.googleapis.com/drive/v3/files",
            params={"supportsAllDrives": "true", "fields": "id,name"},
            headers={**headers, "Content-Type": "application/json"},
            json={
                "name": name,
                "mimeType": "application/vnd.google-apps.folder",
                "parents": [parent],
            },
            timeout=60,
        )
        res.raise_for_status()
        folder_id = res.json()["id"]
        logger.info("drive_subfolder_created", name=name, parent=parent, folder_id=folder_id)

    _folder_cache[key] = folder_id
    return folder_id


def upload_xlsx(filename: str, content: bytes, folder_id: Optional[str] = None) -> dict:
    """Upload an .xlsx to the configured Shared Drive folder (or a subfolder id).

    Returns {"file_id", "link", "name"}.
    """
    if not drive_enabled():
        raise RuntimeError("DRIVE_FOLDER_ID is not configured")

    parent = folder_id or settings.DRIVE_FOLDER_ID
    token = _get_credentials().token

    boundary = "tcg-drive-upload"
    metadata = json.dumps({
        "name": filename,
        "mimeType": XLSX_MIME,
        "parents": [parent],
    })
    body = (
        f"--{boundary}\r\n"
        "Content-Type: application/json; charset=UTF-8\r\n\r\n"
        f"{metadata}\r\n"
        f"--{boundary}\r\n"
        f"Content-Type: {XLSX_MIME}\r\n\r\n"
    ).encode() + content + f"\r\n--{boundary}--".encode()

    res = httpx.post(
        "https://www.googleapis.com/upload/drive/v3/files",
        params={
            "uploadType": "multipart",
            "supportsAllDrives": "true",
            "fields": "id,name,webViewLink",
        },
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/related; boundary={boundary}",
        },
        content=body,
        timeout=120,
    )
    res.raise_for_status()
    data = res.json()
    logger.info("drive_upload_ok", filename=filename, file_id=data.get("id"))
    return {
        "file_id": data["id"],
        "link": data.get("webViewLink"),
        "name": data.get("name", filename),
    }
