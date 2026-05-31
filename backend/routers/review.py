from fastapi import APIRouter, HTTPException
from ..db.client import get_connection
from ..models import Status

router = APIRouter()


def _row_to_dict(row) -> dict:
    cols = ["id","date","merchant","amount","currency","category","owner",
            "confidence","status","source_file","bank","raw_json","created_at"]
    return dict(zip(cols, row))


@router.get("")
def list_pending():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM transactions WHERE status = 'pending' ORDER BY created_at DESC"
    ).fetchall()
    return [_row_to_dict(r) for r in rows]


@router.post("/{tx_id}/approve")
def approve(tx_id: str):
    conn = get_connection()
    row = conn.execute("SELECT id FROM transactions WHERE id = ?", [tx_id]).fetchone()
    if not row:
        raise HTTPException(404, "Transaction not found")
    conn.execute("UPDATE transactions SET status = 'approved' WHERE id = ?", [tx_id])
    return {"id": tx_id, "status": "approved"}


@router.post("/{tx_id}/reject")
def reject(tx_id: str):
    conn = get_connection()
    row = conn.execute("SELECT id FROM transactions WHERE id = ?", [tx_id]).fetchone()
    if not row:
        raise HTTPException(404, "Transaction not found")
    conn.execute("UPDATE transactions SET status = 'rejected' WHERE id = ?", [tx_id])
    return {"id": tx_id, "status": "rejected"}
