from fastapi import APIRouter, HTTPException
from ..db.client import db_connection

router = APIRouter()


def _row_to_dict(row) -> dict:
    if isinstance(row, dict):
        return dict(row)
    cols = ["id","date","merchant","amount","currency","category","owner",
            "confidence","status","source_file","bank","description","raw_json","created_at"]
    return dict(zip(cols, row))


@router.get("")
def list_pending():
    with db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM transactions WHERE status = 'pending' ORDER BY created_at DESC"
        )
        rows = cur.fetchall()
    return [_row_to_dict(r) for r in rows]


@router.post("/{tx_id}/approve")
def approve(tx_id: str):
    with db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM transactions WHERE id = %s", [tx_id])
        if not cur.fetchone():
            raise HTTPException(404, "Transaction not found")
        cur.execute("UPDATE transactions SET status = 'approved' WHERE id = %s", [tx_id])
        conn.commit()
    return {"id": tx_id, "status": "approved"}


@router.post("/{tx_id}/reject")
def reject(tx_id: str):
    with db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM transactions WHERE id = %s", [tx_id])
        if not cur.fetchone():
            raise HTTPException(404, "Transaction not found")
        cur.execute("UPDATE transactions SET status = 'rejected' WHERE id = %s", [tx_id])
        conn.commit()
    return {"id": tx_id, "status": "rejected"}
