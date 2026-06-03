from typing import Optional
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Query, HTTPException
from ..db.client import get_connection

router = APIRouter()


@router.get("/by_category")
def analytics_by_category(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
):
    """Get spending aggregated by category."""
    conn = get_connection()

    conditions = ["status = 'approved'"]
    params = []

    if date_from:
        conditions.append("date >= ?")
        params.append(date_from)
    if date_to:
        conditions.append("date <= ?")
        params.append(date_to)

    where = "WHERE " + " AND ".join(conditions)

    rows = conn.execute(
        f"""
        SELECT category, SUM(amount) as total
        FROM transactions {where}
        GROUP BY category
        ORDER BY total DESC
        """,
        params
    ).fetchall()

    categories = [
        {"name": row[0] or "Uncategorized", "amount": float(row[1])}
        for row in rows
    ]

    return {"categories": categories}


@router.get("/trends")
def analytics_trends(
    weeks: int = Query(12, ge=1, le=52),
):
    """Get spending trends over N weeks."""
    conn = get_connection()

    # Generate week data for the last N weeks
    weeks_data = []
    today = datetime.now().date()

    for week_offset in range(weeks - 1, -1, -1):
        week_end = today - timedelta(days=week_offset * 7)
        week_start = week_end - timedelta(days=6)

        rows = conn.execute(
            """
            SELECT SUM(amount)
            FROM transactions
            WHERE date >= ? AND date <= ? AND status = 'approved'
            """,
            [week_start, week_end]
        ).fetchall()

        total = float(rows[0][0]) if rows[0][0] else 0.0

        weeks_data.append({
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
            "total_spending": total,
        })

    return {"weeks": weeks_data}
