import base64
from fastapi import APIRouter, HTTPException, UploadFile, File, status
from ..db.client import get_connection, generate_id
from ..models import DocumentResponse
from datetime import datetime

router = APIRouter()


def _row_to_dict(row) -> dict:
    cols = ["id", "transaction_id", "filename", "mime_type", "file_blob", "uploaded_at"]
    if isinstance(row, dict):
        return row
    return dict(zip(cols, row))


@router.get("/{tx_id}/document", response_model=DocumentResponse)
def get_document(tx_id: str):
    """Get the source document attached to a transaction."""
    conn = get_connection()
    tx = conn.execute("SELECT id FROM transactions WHERE id = ?", [tx_id]).fetchone()
    if not tx:
        raise HTTPException(404, "Transaction not found")

    row = conn.execute(
        "SELECT * FROM documents WHERE transaction_id = ?", [tx_id]
    ).fetchone()
    if not row:
        raise HTTPException(404, "No document attached to this transaction")

    doc = _row_to_dict(row)
    return DocumentResponse(
        id=doc["id"],
        transaction_id=doc["transaction_id"],
        filename=doc["filename"],
        mime_type=doc["mime_type"],
        data=base64.b64encode(doc["file_blob"]).decode(),
        uploaded_at=doc["uploaded_at"],
    )


@router.post("/{tx_id}/document", status_code=status.HTTP_201_CREATED)
async def upload_document(tx_id: str, file: UploadFile = File(...)):
    """Attach a source document to a transaction."""
    conn = get_connection()
    tx = conn.execute("SELECT id FROM transactions WHERE id = ?", [tx_id]).fetchone()
    if not tx:
        raise HTTPException(404, "Transaction not found")

    existing = conn.execute(
        "SELECT id FROM documents WHERE transaction_id = ?", [tx_id]
    ).fetchone()
    if existing:
        raise HTTPException(409, "Document already attached. Delete existing document first.")

    file_bytes = await file.read()
    doc_id = generate_id()
    conn.execute(
        """INSERT INTO documents (id, transaction_id, filename, mime_type, file_blob, uploaded_at)
        VALUES (?, ?, ?, ?, ?, ?)""",
        [doc_id, tx_id, file.filename, file.content_type or "application/octet-stream",
         file_bytes, datetime.now().isoformat()]
    )
    conn.commit()
    return {"id": doc_id, "transaction_id": tx_id, "filename": file.filename}
