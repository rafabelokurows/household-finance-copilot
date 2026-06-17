import base64
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, UploadFile, File, status
from ..db.client import db_connection, generate_id
from ..models import DocumentResponse

router = APIRouter()


@router.get("/{tx_id}/document", response_model=DocumentResponse)
def get_document(tx_id: str):
    with db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM transactions WHERE id = %s", [tx_id])
        if not cur.fetchone():
            raise HTTPException(404, "Transaction not found")

        cur.execute("SELECT * FROM documents WHERE transaction_id = %s", [tx_id])
        row = cur.fetchone()

    if not row:
        raise HTTPException(404, "No document attached to this transaction")

    return DocumentResponse(
        id=row["id"],
        transaction_id=row["transaction_id"],
        filename=row["filename"],
        mime_type=row["mime_type"],
        data=base64.b64encode(bytes(row["file_blob"])).decode(),
        uploaded_at=row["uploaded_at"],
    )


@router.post("/{tx_id}/document", status_code=status.HTTP_201_CREATED)
async def upload_document(tx_id: str, file: UploadFile = File(...)):
    with db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM transactions WHERE id = %s", [tx_id])
        if not cur.fetchone():
            raise HTTPException(404, "Transaction not found")

        cur.execute("SELECT id FROM documents WHERE transaction_id = %s", [tx_id])
        if cur.fetchone():
            raise HTTPException(409, "Document already attached. Delete existing document first.")

        file_bytes = await file.read()
        doc_id = generate_id()
        cur.execute(
            """INSERT INTO documents (id, transaction_id, filename, mime_type, file_blob, uploaded_at)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            [doc_id, tx_id, file.filename, file.content_type or "application/octet-stream",
             file_bytes, datetime.now(timezone.utc)]
        )
        conn.commit()

    return {"id": doc_id, "transaction_id": tx_id, "filename": file.filename}
