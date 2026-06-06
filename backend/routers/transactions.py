from typing import Optional
from datetime import date
from fastapi import APIRouter, HTTPException, Query
from ..db.client import get_connection
from ..models import TransactionUpdate, Owner, Status, Category

router = APIRouter()


def _row_to_dict(row) -> dict:
    cols = ["id","date","merchant","amount","currency","category","owner",
            "confidence","status","source_file","bank","description","raw_json","created_at"]
    if isinstance(row, dict):
        return row
    return dict(zip(cols, row))


def _attach_tags(conn, tx_dicts: list[dict]) -> list[dict]:
    """Add tags list to each transaction dict."""
    if not tx_dicts:
        return tx_dicts
    ids = [tx["id"] for tx in tx_dicts]
    placeholders = ",".join("?" * len(ids))
    rows = conn.execute(
        f"SELECT transaction_id, tag_name FROM transaction_tags WHERE transaction_id IN ({placeholders})",
        ids,
    ).fetchall()
    tags_by_tx: dict[str, list[str]] = {}
    for tx_id, tag_name in rows:
        tags_by_tx.setdefault(tx_id, []).append(tag_name)
    for tx in tx_dicts:
        tx["tags"] = tags_by_tx.get(tx["id"], [])
    return tx_dicts


# IMPORTANT: Place specific routes BEFORE /{tx_id} so they match first!

@router.get("/pending")
def list_pending_transactions(
    sort_by: str = Query("date"),
    sort_order: str = Query("desc"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
):
    """Get pending transactions with pagination and sorting."""
    conn = get_connection()

    # Validate sort_by
    valid_sort_fields = ["date", "amount", "confidence", "created_at"]
    if sort_by not in valid_sort_fields:
        sort_by = "date"

    # Validate sort_order
    if sort_order.lower() not in ["asc", "desc"]:
        sort_order = "desc"

    offset = (page - 1) * limit

    # Get total count
    total = conn.execute(
        f"SELECT COUNT(*) FROM transactions WHERE status = 'pending'"
    ).fetchone()[0]

    # Get paginated results
    rows = conn.execute(
        f"SELECT * FROM transactions WHERE status = 'pending' "
        f"ORDER BY {sort_by} {sort_order.upper()} LIMIT ? OFFSET ?",
        [limit, offset]
    ).fetchall()

    return {
        "transactions": _attach_tags(conn, [_row_to_dict(r) for r in rows]),
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.get("/processed")
def list_processed_transactions(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    sort_by: str = Query("date"),
    sort_order: str = Query("desc"),
):
    """Get processed (approved/rejected) transactions."""
    conn = get_connection()

    conditions = ["status IN ('approved', 'rejected')"]
    params = []

    if date_from:
        conditions.append("date >= ?")
        params.append(date_from)
    if date_to:
        conditions.append("date <= ?")
        params.append(date_to)

    where = "WHERE " + " AND ".join(conditions)

    # Validate sort_by
    valid_sort_fields = ["date", "amount", "created_at"]
    if sort_by not in valid_sort_fields:
        sort_by = "date"

    if sort_order.lower() not in ["asc", "desc"]:
        sort_order = "desc"

    rows = conn.execute(
        f"SELECT * FROM transactions {where} "
        f"ORDER BY {sort_by} {sort_order.upper()}",
        params
    ).fetchall()

    return {
        "transactions": _attach_tags(conn, [_row_to_dict(r) for r in rows]),
    }


@router.post("/poll_email")
def poll_email():
    """Manually trigger a Gmail poll cycle."""
    from ..ingestion.gmail_poller import trigger_poll
    try:
        new_count = trigger_poll()
        return {"new_transactions": new_count, "status": "checked"}
    except RuntimeError as e:
        raise HTTPException(503, str(e))


@router.get("/export")
def export_transactions(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    format: str = Query("csv"),
):
    """Export transactions as CSV."""
    conn = get_connection()

    conditions = []
    params = []

    if date_from:
        conditions.append("date >= ?")
        params.append(date_from)
    if date_to:
        conditions.append("date <= ?")
        params.append(date_to)

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    rows = conn.execute(
        f"SELECT * FROM transactions {where} ORDER BY date DESC",
        params
    ).fetchall()

    # Build CSV content
    import csv
    from io import StringIO

    output = StringIO()
    cols = ["id", "date", "merchant", "amount", "currency", "category", "owner",
            "confidence", "status", "source_file", "bank", "description", "raw_json", "created_at"]

    writer = csv.DictWriter(output, fieldnames=cols)
    writer.writeheader()

    for row in rows:
        row_dict = _row_to_dict(row)
        writer.writerow(row_dict)

    return output.getvalue()


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
    return _attach_tags(conn, [_row_to_dict(r) for r in rows])


@router.get("/statements")
def list_statements():
    """One row per source file with aggregated transaction metadata."""
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT
            t.source_file                   AS filename,
            t.bank,
            COUNT(t.id)                     AS tx_count,
            MIN(t.date)                     AS period_start,
            MAX(t.date)                     AS period_end,
            MIN(t.created_at)               AS processed_at,
            d.uploaded_at,
            d.mime_type
        FROM transactions t
        LEFT JOIN documents d ON d.filename = t.source_file
        WHERE t.source_file IS NOT NULL
        GROUP BY t.source_file
        ORDER BY MIN(t.created_at) DESC
        """
    ).fetchall()
    return [dict(r) for r in rows]


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
    conn.commit()
    row = conn.execute("SELECT * FROM transactions WHERE id = ?", [tx_id]).fetchone()
    return _row_to_dict(row)


@router.delete("/{tx_id}", status_code=204)
def delete_transaction(tx_id: str):
    conn = get_connection()
    existing = conn.execute("SELECT id FROM transactions WHERE id = ?", [tx_id]).fetchone()
    if not existing:
        raise HTTPException(404, "Transaction not found")
    conn.execute("DELETE FROM transactions WHERE id = ?", [tx_id])
    conn.commit()


@router.post("/{tx_id}/approve")
def approve_transaction(tx_id: str):
    """Approve a transaction."""
    conn = get_connection()
    row = conn.execute("SELECT id FROM transactions WHERE id = ?", [tx_id]).fetchone()
    if not row:
        raise HTTPException(404, "Transaction not found")
    conn.execute("UPDATE transactions SET status = 'approved' WHERE id = ?", [tx_id])
    conn.commit()
    return {"id": tx_id, "status": "approved"}


@router.post("/{tx_id}/reject")
def reject_transaction(tx_id: str):
    """Reject a transaction."""
    conn = get_connection()
    row = conn.execute("SELECT id FROM transactions WHERE id = ?", [tx_id]).fetchone()
    if not row:
        raise HTTPException(404, "Transaction not found")
    conn.execute("UPDATE transactions SET status = 'rejected' WHERE id = ?", [tx_id])
    conn.commit()
    return {"id": tx_id, "status": "rejected"}
