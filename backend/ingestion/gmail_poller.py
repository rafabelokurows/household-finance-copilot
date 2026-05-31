"""Gmail API poller — polls inbox every POLL_INTERVAL seconds for new bank statements."""
import os
import re
import base64
import logging
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from dotenv import load_dotenv

from ..ingestion.extractor import extract_from_bytes, get_mime_type
from ..db.client import get_connection, generate_id
from ..models import Owner, Status

load_dotenv()

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
CREDENTIALS_PATH = os.getenv("GMAIL_CREDENTIALS_PATH", "credentials.json")
TOKEN_PATH = "token.json"
POLL_INTERVAL = int(os.getenv("GMAIL_POLL_INTERVAL", "300"))  # seconds
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.90"))
ATTACHMENTS_DIR = Path(os.getenv("ATTACHMENTS_DIR", "data/attachments"))

SUPPORTED_MIME_TYPES = {
    "image/png", "image/jpeg", "application/pdf", "image/webp"
}

_OWNER_PATTERN = re.compile(r"\[(Rafael|Heloisa|Shared)\]", re.IGNORECASE)


def _get_gmail_service():
    """Authenticate and return Gmail API service."""
    creds = None
    if Path(TOKEN_PATH).exists():
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        Path(TOKEN_PATH).write_text(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def _parse_owner(subject: str) -> Owner | None:
    """Extract owner from email subject like '[Rafael] Bank Statement'."""
    match = _OWNER_PATTERN.search(subject)
    if match:
        name = match.group(1).capitalize()
        try:
            return Owner(name)
        except ValueError:
            return None
    return None


def _process_attachment(
    service,
    message_id: str,
    attachment_id: str,
    filename: str,
    mime_type: str,
    owner: Owner | None,
) -> int:
    """Download attachment, extract transactions, store in DuckDB. Returns count stored."""
    att = service.users().messages().attachments().get(
        userId="me", messageId=message_id, id=attachment_id
    ).execute()
    file_bytes = base64.urlsafe_b64decode(att["data"])

    ATTACHMENTS_DIR.mkdir(parents=True, exist_ok=True)
    save_path = ATTACHMENTS_DIR / filename
    save_path.write_bytes(file_bytes)

    result = extract_from_bytes(file_bytes, filename, mime_type)

    conn = get_connection()
    stored = 0
    for tx in result.transactions:
        if tx.date is None or tx.amount is None or tx.merchant is None:
            logger.warning("Skipping incomplete transaction from %s: %s", filename, tx)
            continue

        status = (
            Status.approved if tx.confidence >= CONFIDENCE_THRESHOLD else Status.pending
        )
        conn.execute(
            """
            INSERT INTO transactions
                (id, date, merchant, amount, currency, category, owner,
                 confidence, status, source_file, bank, raw_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                generate_id(),
                tx.date,
                tx.merchant,
                float(tx.amount),
                tx.currency.value,
                None,
                owner.value if owner else None,
                tx.confidence,
                status.value,
                filename,
                result.bank_detected,
                None,
                datetime.now(timezone.utc),
            ],
        )
        stored += 1
    return stored


def poll_once(service) -> int:
    """Check inbox for unread messages with attachments. Returns total transactions stored."""
    total = 0
    results = service.users().messages().list(
        userId="me",
        q="is:unread has:attachment",
        maxResults=50,
    ).execute()

    messages = results.get("messages", [])
    for msg_stub in messages:
        msg = service.users().messages().get(
            userId="me", id=msg_stub["id"], format="full"
        ).execute()

        headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
        subject = headers.get("Subject", "")
        owner = _parse_owner(subject)

        parts = msg["payload"].get("parts", [])
        for part in parts:
            if part.get("filename") and part.get("body", {}).get("attachmentId"):
                mime = part.get("mimeType", "")
                if mime not in SUPPORTED_MIME_TYPES:
                    continue
                filename = part["filename"]
                att_id = part["body"]["attachmentId"]
                try:
                    count = _process_attachment(
                        service, msg_stub["id"], att_id, filename, mime, owner
                    )
                    total += count
                except Exception:
                    logger.exception("Failed to process attachment %s", filename)

        service.users().messages().modify(
            userId="me",
            id=msg_stub["id"],
            body={"removeLabelIds": ["UNREAD"]},
        ).execute()

    return total


def start_polling() -> threading.Thread | None:
    """Start background polling thread. Returns thread (daemon) or None if credentials missing."""
    if not Path(CREDENTIALS_PATH).exists():
        logger.warning(
            "Gmail credentials not found at %s — email polling disabled.", CREDENTIALS_PATH
        )
        return None

    def _loop():
        service = _get_gmail_service()
        logger.info("Gmail polling started (interval: %ds)", POLL_INTERVAL)
        while True:
            try:
                count = poll_once(service)
                if count:
                    logger.info("Gmail poll: stored %d transactions", count)
            except Exception:
                logger.exception("Gmail poll error")
            time.sleep(POLL_INTERVAL)

    t = threading.Thread(target=_loop, daemon=True, name="gmail-poller")
    t.start()
    return t
