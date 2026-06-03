"""Gmail API poller — polls for bank statement emails with attachments."""
import base64
import logging
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

CREDENTIALS_PATH = os.getenv("GMAIL_CREDENTIALS_PATH", "credentials.json")
TOKEN_PATH = os.getenv("GMAIL_TOKEN_PATH", "token.json")
POLL_INTERVAL = int(os.getenv("GMAIL_POLL_INTERVAL", "300"))
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.90"))

ATTACHMENT_MIME_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/webp",
}


def _get_credentials():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    creds = None
    if Path(TOKEN_PATH).exists():
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())

    return creds


def _get_parts(payload):
    """Recursively collect all leaf parts from a message payload."""
    parts = []
    if payload.get("mimeType", "").startswith("multipart/"):
        for part in payload.get("parts", []):
            parts.extend(_get_parts(part))
    else:
        parts.append(payload)
    return parts


def _poll_once(service, last_poll_time: datetime) -> None:
    from ..db.client import generate_id, get_connection
    from ..ingestion.extractor import extract_from_bytes
    from ..models import Status

    after_ts = int(last_poll_time.timestamp())
    query = f"has:attachment after:{after_ts}"

    try:
        results = service.users().messages().list(userId="me", q=query).execute()
        messages = results.get("messages", [])
    except Exception as e:
        logger.error("Gmail list failed: %s", e)
        return

    stored_total = 0
    for msg_meta in messages:
        msg_id = msg_meta["id"]
        try:
            msg = service.users().messages().get(
                userId="me", id=msg_id, format="full"
            ).execute()
        except Exception as e:
            logger.error("Failed to fetch message %s: %s", msg_id, e)
            continue

        for part in _get_parts(msg.get("payload", {})):
            mime = part.get("mimeType", "")
            if mime not in ATTACHMENT_MIME_TYPES:
                continue

            filename = part.get("filename") or f"attachment_{msg_id}"
            body = part.get("body", {})
            attachment_id = body.get("attachmentId")

            try:
                if attachment_id:
                    att = service.users().messages().attachments().get(
                        userId="me", messageId=msg_id, id=attachment_id
                    ).execute()
                    file_bytes = base64.urlsafe_b64decode(att["data"] + "==")
                else:
                    file_bytes = base64.urlsafe_b64decode(body.get("data", "") + "==")
            except Exception as e:
                logger.error("Failed to decode attachment %s/%s: %s", msg_id, filename, e)
                continue

            result = extract_from_bytes(file_bytes, filename, mime)

            conn = get_connection()
            try:
                for tx in result.transactions:
                    if tx.date is None or tx.amount is None or tx.merchant is None:
                        continue
                    status = (
                        Status.approved
                        if tx.confidence >= CONFIDENCE_THRESHOLD
                        else Status.pending
                    )
                    tx_id = generate_id()
                    conn.execute(
                        """INSERT INTO transactions
                           (id, date, merchant, amount, currency, category, owner,
                            confidence, status, source_file, bank, raw_json, created_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        [
                            tx_id, tx.date, tx.merchant, float(tx.amount),
                            tx.currency.value, None, None, tx.confidence,
                            status.value, filename, result.bank_detected,
                            None, datetime.now(timezone.utc),
                        ],
                    )
                    conn.execute(
                        """INSERT INTO documents
                           (id, transaction_id, filename, mime_type, file_blob, uploaded_at)
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        [
                            generate_id(), tx_id, filename, mime, file_bytes,
                            datetime.now(timezone.utc).isoformat(),
                        ],
                    )
                    stored_total += 1
                conn.commit()
            finally:
                conn.close()

    if stored_total:
        logger.info("Gmail poll: stored %d transactions from new emails", stored_total)


def _polling_loop() -> None:
    from googleapiclient.discovery import build

    try:
        creds = _get_credentials()
        service = build("gmail", "v1", credentials=creds)
    except Exception as e:
        logger.error("Gmail authentication failed: %s", e)
        return

    logger.info("Gmail polling started (interval: %ds)", POLL_INTERVAL)
    last_poll = datetime.now(timezone.utc)

    while True:
        try:
            _poll_once(service, last_poll)
        except Exception as e:
            logger.error("Gmail poll cycle error: %s", e)
        last_poll = datetime.now(timezone.utc)
        time.sleep(POLL_INTERVAL)


def start_polling():
    """Start Gmail polling in a daemon background thread. No-op if credentials not found."""
    if not Path(CREDENTIALS_PATH).exists():
        logger.info("Gmail polling disabled: credentials.json not found at %s", CREDENTIALS_PATH)
        return None

    try:
        import google.oauth2.credentials  # noqa: F401
        import google_auth_oauthlib  # noqa: F401
        import googleapiclient  # noqa: F401
    except ImportError:
        logger.warning("Gmail polling disabled: google-auth libraries not installed")
        return None

    thread = threading.Thread(target=_polling_loop, daemon=True)
    thread.start()
    logger.info("Gmail polling thread started")
    return thread
