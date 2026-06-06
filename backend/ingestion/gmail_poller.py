"""Gmail API poller — polls for bank statement emails with attachments."""
import base64
import hashlib
import logging
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

_poll_lock = threading.Lock()

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

CREDENTIALS_PATH = os.getenv("GMAIL_CREDENTIALS_PATH", "credentials.json")
TOKEN_PATH = os.getenv("GMAIL_TOKEN_PATH", "token.json")
POLL_INTERVAL = int(os.getenv("GMAIL_POLL_INTERVAL", "300"))
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.90"))
RESCAN_FROM = os.getenv("GMAIL_RESCAN_FROM")  # e.g. "2026-01-01" — overrides stored last_poll floor

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
    token_path = Path(TOKEN_PATH)
    if token_path.exists():
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
        except Exception:
            logger.warning("token.json corrupted — deleting and re-authenticating")
            token_path.unlink()
            creds = None

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


def _load_last_poll(conn) -> datetime:
    logger.info("RESCAN_FROM module value: %r", RESCAN_FROM)
    if RESCAN_FROM:
        try:
            dt = datetime.fromisoformat(RESCAN_FROM).replace(tzinfo=timezone.utc)
            logger.info("GMAIL_RESCAN_FROM set — scanning from %s", dt.isoformat())
            return dt
        except ValueError:
            logger.warning("Invalid GMAIL_RESCAN_FROM value %r — ignoring", RESCAN_FROM)
    row = conn.execute(
        "SELECT value FROM gmail_poll_state WHERE key = 'last_poll'"
    ).fetchone()
    if row:
        return datetime.fromisoformat(row[0])
    return datetime.now(timezone.utc)


def _save_last_poll(conn, dt: datetime) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO gmail_poll_state (key, value) VALUES ('last_poll', ?)",
        [dt.isoformat()],
    )
    conn.commit()


def _is_processed(conn, msg_id: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM gmail_processed_messages WHERE message_id = ?", [msg_id]
    ).fetchone() is not None


def _mark_processed(conn, msg_id: str) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO gmail_processed_messages (message_id, processed_at) VALUES (?, ?)",
        [msg_id, datetime.now(timezone.utc).isoformat()],
    )


def _is_attachment_processed(conn, content_hash: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM processed_attachments WHERE content_hash = ?", [content_hash]
    ).fetchone() is not None


def _mark_attachment_processed(conn, content_hash: str, filename: str) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO processed_attachments (content_hash, filename, processed_at) VALUES (?, ?, ?)",
        [content_hash, filename, datetime.now(timezone.utc).isoformat()],
    )


def _poll_once(service, last_poll_time: datetime) -> None:
    if not _poll_lock.acquire(blocking=False):
        logger.info("Poll already in progress — skipping")
        return
    try:
        _poll_once_inner(service, last_poll_time)
    finally:
        _poll_lock.release()


def _poll_once_inner(service, last_poll_time: datetime) -> None:
    from ..db.client import generate_id, get_connection
    from ..ingestion.extractor import extract_from_bytes
    from ..ingestion.category_rules import guess_category
    from ..models import Status

    conn = get_connection()
    after_ts = int(last_poll_time.timestamp())
    query = (
        f"from:(rafabelokurows@gmail.com OR rafadv123@gmail.com OR heloisa.aantunes@gmail.com)"
        f" has:attachment after:{after_ts}"
    )

    logger.info("Gmail query: %s", query)
    results = service.users().messages().list(userId="me", q=query).execute()
    messages = results.get("messages", [])
    logger.info("Gmail query returned %d message(s)", len(messages))

    stored_total = 0
    for msg_meta in messages:
        msg_id = msg_meta["id"]

        if _is_processed(conn, msg_id):
            logger.info("Message %s already processed — skipping", msg_id)
            continue

        logger.info("Processing message %s", msg_id)
        try:
            msg = service.users().messages().get(
                userId="me", id=msg_id, format="full"
            ).execute()
        except Exception as e:
            logger.error("Failed to fetch message %s: %s", msg_id, e)
            continue

        parts = _get_parts(msg.get("payload", {}))
        attachment_parts = [p for p in parts if p.get("mimeType", "") in ATTACHMENT_MIME_TYPES]
        logger.info("Message %s has %d eligible attachment(s)", msg_id, len(attachment_parts))

        extraction_failed = False
        for part in attachment_parts:
            mime = part.get("mimeType", "")
            filename = part.get("filename") or f"attachment_{msg_id}"
            body = part.get("body", {})
            attachment_id = body.get("attachmentId")

            logger.info("Downloading attachment %s (mime=%s)", filename, mime)
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

            logger.info("Attachment %s downloaded (%d bytes)", filename, len(file_bytes))
            content_hash = hashlib.sha256(file_bytes).hexdigest()
            if _is_attachment_processed(conn, content_hash):
                logger.info("Skipping duplicate attachment %s (hash=%s...)", filename, content_hash[:8])
                continue

            logger.info("Extracting transactions from %s", filename)
            result = extract_from_bytes(file_bytes, filename, mime)

            if result.extraction_notes and result.extraction_notes.startswith("Extraction error:"):
                logger.warning("Extraction failed for %s/%s — will retry next poll", msg_id, filename)
                extraction_failed = True
                continue

            valid_txs = [
                tx for tx in result.transactions
                if tx.date is not None and tx.amount is not None and tx.merchant is not None
            ]

            logger.info("Extraction complete: %d raw, %d valid transactions from %s",
                        len(result.transactions), len(valid_txs), filename)

            if not valid_txs:
                logger.warning("No valid transactions extracted from %s — skipping", filename)
                continue

            first_tx_id = None
            for i, tx in enumerate(valid_txs):
                status = (
                    Status.approved
                    if tx.confidence >= CONFIDENCE_THRESHOLD
                    else Status.pending
                )
                tx_id = generate_id()
                if i == 0:
                    first_tx_id = tx_id
                conn.execute(
                    """INSERT INTO transactions
                       (id, date, merchant, amount, currency, category, owner,
                        confidence, status, source_file, bank, raw_json, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    [
                        tx_id, tx.date, tx.merchant, float(tx.amount),
                        tx.currency.value, guess_category(tx.merchant), None, tx.confidence,
                        status.value, filename, result.bank_detected,
                        None, datetime.now(timezone.utc),
                    ],
                )
                stored_total += 1

            _mark_attachment_processed(conn, content_hash, filename)

            # Store BLOB once per attachment, linked to first transaction only
            conn.execute(
                """INSERT INTO documents
                   (id, transaction_id, filename, mime_type, file_blob, uploaded_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                [
                    generate_id(), first_tx_id, filename, mime, file_bytes,
                    datetime.now(timezone.utc).isoformat(),
                ],
            )

        if not extraction_failed:
            _mark_processed(conn, msg_id)
        conn.commit()

    if stored_total:
        logger.info("Gmail poll: stored %d transactions from new emails", stored_total)


def _polling_loop() -> None:
    from googleapiclient.discovery import build
    from ..db.client import get_connection

    try:
        creds = _get_credentials()
        service = build("gmail", "v1", credentials=creds)
    except Exception as e:
        logger.error("Gmail authentication failed: %s", e)
        return

    conn = get_connection()
    last_poll = _load_last_poll(conn)
    logger.info(
        "Gmail polling started (interval: %ds, resuming from %s)",
        POLL_INTERVAL,
        last_poll.isoformat(),
    )

    while True:
        poll_start = datetime.now(timezone.utc)
        try:
            _poll_once(service, last_poll)
            _save_last_poll(conn, poll_start)
            last_poll = poll_start
        except Exception as e:
            logger.error("Gmail poll cycle error: %s", e)
            # last_poll NOT advanced — same window retried next cycle
        time.sleep(POLL_INTERVAL)


def trigger_poll() -> int:
    """Manually trigger one poll cycle. Returns number of new transactions stored. Thread-safe."""
    from googleapiclient.discovery import build
    from ..db.client import get_connection

    if not Path(CREDENTIALS_PATH).exists():
        raise RuntimeError("Gmail credentials not configured")

    try:
        creds = _get_credentials()
        service = build("gmail", "v1", credentials=creds)
    except Exception as e:
        raise RuntimeError(f"Gmail authentication failed: {e}") from e

    conn = get_connection()
    last_poll = _load_last_poll(conn)

    before = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
    _poll_once(service, last_poll)
    after = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]

    poll_start = datetime.now(timezone.utc)
    _save_last_poll(conn, poll_start)

    return after - before


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
