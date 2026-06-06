from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..db.client import get_connection

router = APIRouter()

VALID_CATEGORIES = {
    "Groceries", "Restaurants", "Transportation", "Utilities", "Shopping",
    "Entertainment", "Healthcare", "Travel", "Insurance", "Salary",
    "Bonus", "Investments", "Other",
}


def _get_rules(conn) -> list[dict]:
    rows = conn.execute(
        "SELECT category, keyword FROM category_rules ORDER BY priority, id"
    ).fetchall()
    grouped: dict[str, list[str]] = {}
    for category, keyword in rows:
        grouped.setdefault(category, []).append(keyword)
    return [{"category": cat, "keywords": kws} for cat, kws in grouped.items()]


@router.get("/rules")
def get_rules():
    return _get_rules(get_connection())


class KeywordPayload(BaseModel):
    keyword: str


@router.post("/rules/{category}/keywords", status_code=201)
def add_keyword(category: str, body: KeywordPayload):
    if category not in VALID_CATEGORIES:
        raise HTTPException(400, f"Unknown category: {category}")
    keyword = body.keyword.strip().lower()
    if not keyword:
        raise HTTPException(400, "Keyword cannot be empty")
    conn = get_connection()
    max_priority = conn.execute("SELECT COALESCE(MAX(priority), -1) FROM category_rules").fetchone()[0]
    try:
        conn.execute(
            "INSERT INTO category_rules (category, keyword, priority) VALUES (?, ?, ?)",
            [category, keyword, max_priority + 1],
        )
        conn.commit()
    except Exception:
        raise HTTPException(409, f"Keyword '{keyword}' already exists in {category}")
    return _get_rules(conn)


@router.delete("/rules/{category}/keywords/{keyword}")
def remove_keyword(category: str, keyword: str):
    conn = get_connection()
    result = conn.execute(
        "DELETE FROM category_rules WHERE category = ? AND keyword = ?",
        [category, keyword],
    )
    conn.commit()
    if result.rowcount == 0:
        raise HTTPException(404, f"Keyword '{keyword}' not found in {category}")
    return _get_rules(conn)
