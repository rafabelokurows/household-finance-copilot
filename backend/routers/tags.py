from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..db.client import get_connection

router = APIRouter()


class TagsPayload(BaseModel):
    tags: list[str]


@router.get("/tags")
def list_tags():
    """Return all known tag names for autocomplete."""
    conn = get_connection()
    rows = conn.execute("SELECT name FROM tags ORDER BY name").fetchall()
    return {"tags": [r[0] for r in rows]}


@router.get("/transactions/{tx_id}/tags")
def get_transaction_tags(tx_id: str):
    conn = get_connection()
    _require_transaction(conn, tx_id)
    rows = conn.execute(
        "SELECT tag_name FROM transaction_tags WHERE transaction_id = ? ORDER BY tag_name",
        [tx_id],
    ).fetchall()
    return {"tags": [r[0] for r in rows]}


@router.put("/transactions/{tx_id}/tags")
def set_transaction_tags(tx_id: str, body: TagsPayload):
    """Replace all tags for a transaction atomically."""
    conn = get_connection()
    _require_transaction(conn, tx_id)

    tags = [t.strip().lower() for t in body.tags if t.strip()]

    for tag in tags:
        conn.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", [tag])

    conn.execute(
        "DELETE FROM transaction_tags WHERE transaction_id = ?", [tx_id]
    )
    for tag in tags:
        conn.execute(
            "INSERT INTO transaction_tags (transaction_id, tag_name) VALUES (?, ?)",
            [tx_id, tag],
        )

    conn.commit()
    return {"transaction_id": tx_id, "tags": tags}


def _require_transaction(conn, tx_id: str):
    if not conn.execute("SELECT 1 FROM transactions WHERE id = ?", [tx_id]).fetchone():
        raise HTTPException(404, "Transaction not found")
