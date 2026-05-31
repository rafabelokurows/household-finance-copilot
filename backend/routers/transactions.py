from typing import Optional
from datetime import date
from fastapi import APIRouter, HTTPException, Query
from ..db.client import get_connection
from ..models import TransactionUpdate, Owner, Status, Category

router = APIRouter()


def _row_to_dict(row) -> dict:
    cols = ["id","date","merchant","amount","currency","category","owner",
            "confidence","status","source_file","bank","raw_json","created_at"]
    return dict(zip(cols, row))


@router.get("")
def list_transactions(
    owner: Optional[Owner] = Query(None),
    status: Optional[Status] = Query(None),
    category: Optional[Category] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    conn = get_connection()
    conditions, params = [], []
    if owner:
        conditions.append("owner = ?"); params.append(owner.value)
    if status:
        conditions.append("status = ?"); params.append(status.value)
    if category:
        conditions.append("category = ?"); params.append(category.value)
    if date_from:
        conditions.append("date >= ?"); params.append(date_from)
    if date_to:
        conditions.append("date <= ?"); params.append(date_to)

    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    rows = conn.execute(
        f"SELECT * FROM transactions {where} ORDER BY date DESC, created_at DESC LIMIT ? OFFSET ?",
        params + [limit, offset]
    ).fetchall()
    return [_row_to_dict(r) for r in rows]


@router.get("/{tx_id}")
def get_transaction(tx_id: str):
    conn = get_connection()
    row = conn.execute("SELECT * FROM transactions WHERE id = ?", [tx_id]).fetchone()
    if not row:
        raise HTTPException(404, "Transaction not found")
    return _row_to_dict(row)


@router.patch("/{tx_id}")
def update_transaction(tx_id: str, body: TransactionUpdate):
    conn = get_connection()
    existing = conn.execute("SELECT id FROM transactions WHERE id = ?", [tx_id]).fetchone()
    if not existing:
        raise HTTPException(404, "Transaction not found")

    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(400, "No fields to update")

    set_clauses = [f"{k} = ?" for k in updates]
    params = [v.value if hasattr(v, 'value') else v for v in updates.values()]
    # convert date/Decimal to native types
    params = [float(p) if hasattr(p, 'quantize') else p for p in params]
    params.append(tx_id)

    conn.execute(
        f"UPDATE transactions SET {', '.join(set_clauses)} WHERE id = ?", params
    )
    row = conn.execute("SELECT * FROM transactions WHERE id = ?", [tx_id]).fetchone()
    return _row_to_dict(row)


@router.delete("/{tx_id}", status_code=204)
def delete_transaction(tx_id: str):
    conn = get_connection()
    existing = conn.execute("SELECT id FROM transactions WHERE id = ?", [tx_id]).fetchone()
    if not existing:
        raise HTTPException(404, "Transaction not found")
    conn.execute("DELETE FROM transactions WHERE id = ?", [tx_id])
