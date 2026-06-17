from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..db.client import db_connection

router = APIRouter()

VALID_CATEGORIES = {
    "Groceries", "Restaurants", "Transportation", "Utilities", "Shopping",
    "Entertainment", "Healthcare", "Travel", "Insurance", "Salary",
    "Bonus", "Investments", "Other",
}


def _get_rules(conn) -> list[dict]:
    cur = conn.cursor()
    cur.execute("SELECT category, keyword FROM category_rules ORDER BY priority, id")
    rows = cur.fetchall()
    grouped: dict[str, list[str]] = {}
    for row in rows:
        grouped.setdefault(row["category"], []).append(row["keyword"])
    return [{"category": cat, "keywords": kws} for cat, kws in grouped.items()]


@router.get("/rules")
def get_rules():
    with db_connection() as conn:
        return _get_rules(conn)


class KeywordPayload(BaseModel):
    keyword: str


@router.post("/rules/{category}/keywords", status_code=201)
def add_keyword(category: str, body: KeywordPayload):
    if category not in VALID_CATEGORIES:
        raise HTTPException(400, f"Unknown category: {category}")
    keyword = body.keyword.strip().lower()
    if not keyword:
        raise HTTPException(400, "Keyword cannot be empty")

    with db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COALESCE(MAX(priority), -1) AS max_priority FROM category_rules")
        max_priority = cur.fetchone()["max_priority"]
        try:
            cur.execute(
                "INSERT INTO category_rules (category, keyword, priority) VALUES (%s, %s, %s)",
                [category, keyword, max_priority + 1],
            )
            conn.commit()
        except Exception:
            raise HTTPException(409, f"Keyword '{keyword}' already exists in {category}")
        return _get_rules(conn)


@router.delete("/rules/{category}/keywords/{keyword}")
def remove_keyword(category: str, keyword: str):
    with db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM category_rules WHERE category = %s AND keyword = %s",
            [category, keyword],
        )
        conn.commit()
        if cur.rowcount == 0:
            raise HTTPException(404, f"Keyword '{keyword}' not found in {category}")
        return _get_rules(conn)
