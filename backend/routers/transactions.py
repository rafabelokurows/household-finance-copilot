from typing import Optional
from datetime import date
from fastapi import APIRouter, HTTPException, Query
from ..db.client import db_connection
from ..models import TransactionUpdate, Owner, Status, Category

router = APIRouter()


def _row_to_dict(row) -> dict:
    if isinstance(row, dict):
        return dict(row)
    cols = ["id","date","merchant","amount","currency","category","owner",
            "confidence","status","source_file","bank","description","raw_json","created_at"]
    return dict(zip(cols, row))


def _attach_tags(conn, tx_dicts: list[dict]) -> list[dict]:
    if not tx_dicts:
        return tx_dicts
    ids = [tx["id"] for tx in tx_dicts]
    placeholders = ",".join(["%s"] * len(ids))
    cur = conn.cursor()
    cur.execute(
        f"SELECT transaction_id, tag_name FROM transaction_tags WHERE transaction_id IN ({placeholders})",
        tuple(ids),
    )
    rows = cur.fetchall()
    tags_by_tx: dict[str, list[str]] = {}
    for row in rows:
        tags_by_tx.setdefault(row["transaction_id"], []).append(row["tag_name"])
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
    valid_sort_fields = ["date", "amount", "confidence", "created_at"]
    if sort_by not in valid_sort_fields:
        sort_by = "date"
    if sort_order.lower() not in ["asc", "desc"]:
        sort_order = "desc"

    offset = (page - 1) * limit

    with db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) AS count FROM transactions WHERE status = 'pending'")
        total = cur.fetchone()["count"]

        cur.execute(
            f"SELECT * FROM transactions WHERE status = 'pending' "
            f"ORDER BY {sort_by} {sort_order.upper()} LIMIT %s OFFSET %s",
            [limit, offset]
        )
        rows = cur.fetchall()

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
    category: Optional[str] = Query(None),
    sort_by: str = Query("date"),
    sort_order: str = Query("desc"),
    limit: Optional[int] = Query(None),
    offset: int = Query(0, ge=0),
):
    conditions = ["status IN ('approved', 'rejected')"]
    params = []

    if date_from:
        conditions.append("date >= %s")
        params.append(date_from)
    if date_to:
        conditions.append("date <= %s")
        params.append(date_to)
    if category:
        conditions.append("category = %s")
        params.append(category)

    where = "WHERE " + " AND ".join(conditions)

    valid_sort_fields = ["date", "amount", "created_at"]
    if sort_by not in valid_sort_fields:
        sort_by = "date"
    if sort_order.lower() not in ["asc", "desc"]:
        sort_order = "desc"

    query = f"SELECT * FROM transactions {where} ORDER BY {sort_by} {sort_order.upper()}"
    if limit:
        query += " LIMIT %s OFFSET %s"
        params.extend([limit, offset])

    with db_connection() as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        rows = cur.fetchall()
        return {
            "transactions": _attach_tags(conn, [_row_to_dict(r) for r in rows]),
        }


@router.post("/poll_email")
def poll_email():
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
    conditions = []
    params = []

    if date_from:
        conditions.append("date >= %s")
        params.append(date_from)
    if date_to:
        conditions.append("date <= %s")
        params.append(date_to)

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    with db_connection() as conn:
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM transactions {where} ORDER BY date DESC", params)
        rows = cur.fetchall()

    import csv
    from io import StringIO

    output = StringIO()
    cols = ["id", "date", "merchant", "amount", "currency", "category", "owner",
            "confidence", "status", "source_file", "bank", "description", "raw_json", "created_at"]

    writer = csv.DictWriter(output, fieldnames=cols)
    writer.writeheader()
    for row in rows:
        writer.writerow(_row_to_dict(row))

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
    conditions, params = [], []
    if owner:
        conditions.append("owner = %s"); params.append(owner.value)
    if status:
        conditions.append("status = %s"); params.append(status.value)
    if category:
        conditions.append("category = %s"); params.append(category.value)
    if date_from:
        conditions.append("date >= %s"); params.append(date_from)
    if date_to:
        conditions.append("date <= %s"); params.append(date_to)

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    with db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            f"SELECT * FROM transactions {where} ORDER BY date DESC, created_at DESC LIMIT %s OFFSET %s",
            params + [limit, offset]
        )
        rows = cur.fetchall()
        return _attach_tags(conn, [_row_to_dict(r) for r in rows])


@router.get("/statements")
def list_statements():
    with db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                t.source_file                   AS filename,
                MAX(t.bank)                     AS bank,
                COUNT(t.id)                     AS tx_count,
                MIN(t.date)                     AS period_start,
                MAX(t.date)                     AS period_end,
                MIN(t.created_at)               AS processed_at,
                MAX(d.uploaded_at)              AS uploaded_at,
                MAX(d.mime_type)                AS mime_type
            FROM transactions t
            LEFT JOIN documents d ON d.filename = t.source_file
            WHERE t.source_file IS NOT NULL
            GROUP BY t.source_file
            ORDER BY MIN(t.created_at) DESC
            """
        )
        rows = cur.fetchall()
    return [dict(r) for r in rows]


@router.get("/{tx_id}")
def get_transaction(tx_id: str):
    with db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM transactions WHERE id = %s", [tx_id])
        row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Transaction not found")
    return _row_to_dict(row)


@router.patch("/{tx_id}")
def update_transaction(tx_id: str, body: TransactionUpdate):
    with db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM transactions WHERE id = %s", [tx_id])
        if not cur.fetchone():
            raise HTTPException(404, "Transaction not found")

        updates = body.model_dump(exclude_none=True)
        if not updates:
            raise HTTPException(400, "No fields to update")

        set_clauses = [f"{k} = %s" for k in updates]
        params = [v.value if hasattr(v, 'value') else v for v in updates.values()]
        params = [float(p) if hasattr(p, 'quantize') else p for p in params]
        params.append(tx_id)

        cur.execute(
            f"UPDATE transactions SET {', '.join(set_clauses)} WHERE id = %s", params
        )
        conn.commit()
        cur.execute("SELECT * FROM transactions WHERE id = %s", [tx_id])
        row = cur.fetchone()
    return _row_to_dict(row)


@router.delete("/{tx_id}", status_code=204)
def delete_transaction(tx_id: str):
    with db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM transactions WHERE id = %s", [tx_id])
        if not cur.fetchone():
            raise HTTPException(404, "Transaction not found")
        cur.execute("DELETE FROM transactions WHERE id = %s", [tx_id])
        conn.commit()


@router.post("/{tx_id}/approve")
def approve_transaction(tx_id: str):
    with db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM transactions WHERE id = %s", [tx_id])
        if not cur.fetchone():
            raise HTTPException(404, "Transaction not found")
        cur.execute("UPDATE transactions SET status = 'approved' WHERE id = %s", [tx_id])
        conn.commit()
    return {"id": tx_id, "status": "approved"}


@router.post("/{tx_id}/reject")
def reject_transaction(tx_id: str):
    with db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM transactions WHERE id = %s", [tx_id])
        if not cur.fetchone():
            raise HTTPException(404, "Transaction not found")
        cur.execute("UPDATE transactions SET status = 'rejected' WHERE id = %s", [tx_id])
        conn.commit()
    return {"id": tx_id, "status": "rejected"}
