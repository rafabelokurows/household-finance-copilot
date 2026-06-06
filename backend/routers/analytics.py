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


@router.get("/by_tag")
def analytics_by_tag(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
):
    """Get spending aggregated by tag."""
    conn = get_connection()

    conditions = ["t.status = 'approved'"]
    params = []

    if date_from:
        conditions.append("t.date >= ?")
        params.append(date_from)
    if date_to:
        conditions.append("t.date <= ?")
        params.append(date_to)

    where = "WHERE " + " AND ".join(conditions)

    rows = conn.execute(
        f"""
        SELECT tt.tag_name, SUM(t.amount) as total
        FROM transaction_tags tt
        JOIN transactions t ON t.id = tt.transaction_id
        {where}
        GROUP BY tt.tag_name
        ORDER BY total DESC
        """,
        params,
    ).fetchall()

    return {"tags": [{"name": row[0], "amount": float(row[1])} for row in rows]}


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


@router.get("/by_month")
def analytics_by_month(months: int = Query(12, ge=1, le=36)):
    """Get monthly spending totals for the last N months."""
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT strftime('%Y-%m', date) AS month, SUM(amount) AS total
        FROM transactions
        WHERE status = 'approved'
        GROUP BY month
        ORDER BY month DESC
        LIMIT ?
        """,
        [months],
    ).fetchall()
    result = [{"month": r[0], "total": float(r[1])} for r in rows]
    result.reverse()
    return {"months": result}


@router.get("/by_owner")
def analytics_by_owner(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
):
    """Get spending totals broken down by owner."""
    conn = get_connection()
    conditions = ["status = 'approved'", "owner IS NOT NULL"]
    params = []
    if date_from:
        conditions.append("date >= ?")
        params.append(date_from)
    if date_to:
        conditions.append("date <= ?")
        params.append(date_to)
    where = "WHERE " + " AND ".join(conditions)
    rows = conn.execute(
        f"SELECT owner, SUM(amount) AS total FROM transactions {where} GROUP BY owner ORDER BY total DESC",
        params,
    ).fetchall()
    return {"owners": [{"owner": r[0], "total": float(r[1])} for r in rows]}


@router.get("/category_trends")
def analytics_category_trends(months: int = Query(6, ge=1, le=24)):
    """Get monthly spending per category for the last N months."""
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT strftime('%Y-%m', date) AS month, category, SUM(amount) AS total
        FROM transactions
        WHERE status = 'approved' AND category IS NOT NULL
        GROUP BY month, category
        ORDER BY month ASC
        """,
    ).fetchall()
    # Filter to last N months
    all_months = sorted({r[0] for r in rows})
    keep_months = set(all_months[-months:])
    trends = [
        {"month": r[0], "category": r[1], "total": float(r[2])}
        for r in rows if r[0] in keep_months
    ]
    return {"trends": trends}
