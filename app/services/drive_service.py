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


def _get_credentials() -> Credentials:
    global _creds
    if _creds is None or not _creds.valid:
        _creds, _ = default_credentials(scopes=[DRIVE_SCOPE])
        _creds.refresh(RefreshRequest())
    return _creds


def drive_enabled() -> bool:
    return bool(getattr(settings, "DRIVE_FOLDER_ID", None))


def upload_xlsx(filename: str, content: bytes) -> dict:
    """Upload an .xlsx to the configured Shared Drive folder.

    Returns {"file_id", "link", "name"}.
    """
    if not drive_enabled():
        raise RuntimeError("DRIVE_FOLDER_ID is not configured")

    token = _get_credentials().token

    boundary = "tcg-drive-upload"
    metadata = json.dumps({
        "name": filename,
        "mimeType": XLSX_MIME,
        "parents": [settings.DRIVE_FOLDER_ID],
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
