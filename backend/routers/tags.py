from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..db.client import db_connection

router = APIRouter()


class TagsPayload(BaseModel):
    tags: list[str]


@router.get("/tags")
def list_tags():
    with db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT name FROM tags ORDER BY name")
        rows = cur.fetchall()
    return {"tags": [r["name"] for r in rows]}


@router.get("/transactions/{tx_id}/tags")
def get_transaction_tags(tx_id: str):
    with db_connection() as conn:
        cur = conn.cursor()
        _require_transaction(cur, tx_id)
        cur.execute(
            "SELECT tag_name FROM transaction_tags WHERE transaction_id = %s ORDER BY tag_name",
            [tx_id],
        )
        rows = cur.fetchall()
    return {"tags": [r["tag_name"] for r in rows]}


@router.put("/transactions/{tx_id}/tags")
def set_transaction_tags(tx_id: str, body: TagsPayload):
    tags = [t.strip().lower() for t in body.tags if t.strip()]

    with db_connection() as conn:
        cur = conn.cursor()
        _require_transaction(cur, tx_id)

        for tag in tags:
            cur.execute(
                "INSERT INTO tags (name) VALUES (%s) ON CONFLICT DO NOTHING", [tag]
            )

        cur.execute("DELETE FROM transaction_tags WHERE transaction_id = %s", [tx_id])
        for tag in tags:
            cur.execute(
                "INSERT INTO transaction_tags (transaction_id, tag_name) VALUES (%s, %s)",
                [tx_id, tag],
            )

        conn.commit()

    return {"transaction_id": tx_id, "tags": tags}


def _require_transaction(cur, tx_id: str):
    cur.execute("SELECT 1 FROM transactions WHERE id = %s", [tx_id])
    if not cur.fetchone():
        raise HTTPException(404, "Transaction not found")
