import os
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, UploadFile, Form, HTTPException

from ..db.client import db_connection, generate_id
from ..ingestion.extractor import extract_from_bytes, get_mime_type
from ..ingestion.category_rules import guess_category
from ..models import Owner, Status

router = APIRouter()
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.90"))
ALLOWED_CONTENT_TYPES = {"image/png", "image/jpeg", "application/pdf", "image/webp"}


@router.post("")
async def upload_file(
    file: UploadFile,
    owner: Optional[str] = Form(None),
):
    owner_enum = None
    if owner:
        try:
            owner_enum = Owner(owner)
        except ValueError:
            raise HTTPException(400, f"Invalid owner '{owner}'. Must be Rafael, Heloisa, or Shared.")

    mime = get_mime_type(file.filename)
    if mime not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(400, f"Unsupported file type: {file.filename}")

    file_bytes = await file.read()
    result = extract_from_bytes(file_bytes, file.filename, mime)

    stored, pending = 0, 0
    inserted = []

    with db_connection() as conn:
        cur = conn.cursor()
        for tx in result.transactions:
            if tx.date is None or tx.amount is None or tx.merchant is None:
                continue
            tx_status = Status.approved if tx.confidence >= CONFIDENCE_THRESHOLD else Status.pending
            tx_id = generate_id()
            cur.execute(
                """INSERT INTO transactions
                   (id, date, merchant, amount, currency, category, owner,
                    confidence, status, source_file, bank, raw_json, created_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                [tx_id, tx.date, tx.merchant, float(tx.amount), tx.currency.value,
                 guess_category(tx.merchant), owner_enum.value if owner_enum else None,
                 tx.confidence, tx_status.value, file.filename,
                 result.bank_detected, None, datetime.now(timezone.utc)],
            )

            cur.execute(
                """INSERT INTO documents (id, transaction_id, filename, mime_type, file_blob, uploaded_at)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                [generate_id(), tx_id, file.filename, mime, file_bytes,
                 datetime.now(timezone.utc)]
            )

            stored += 1
            if tx_status == Status.pending:
                pending += 1
            inserted.append({"id": tx_id, "merchant": tx.merchant,
                             "amount": float(tx.amount), "status": tx_status.value,
                             "confidence": tx.confidence})

        conn.commit()

    return {
        "stored": stored,
        "pending_review": pending,
        "transactions": inserted,
        "notes": result.extraction_notes,
    }
