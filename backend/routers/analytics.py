from typing import Optional
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Query
from ..db.client import db_connection

router = APIRouter()


@router.get("/by_category")
def analytics_by_category(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
):
    conditions = ["status = 'approved'"]
    params = []

    if date_from:
        conditions.append("date >= %s")
        params.append(date_from)
    if date_to:
        conditions.append("date <= %s")
        params.append(date_to)

    where = "WHERE " + " AND ".join(conditions)

    with db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            f"""
            SELECT category, SUM(amount) AS total
            FROM transactions {where}
            GROUP BY category
            ORDER BY total DESC
            """,
            params
        )
        rows = cur.fetchall()

    categories = [
        {"name": row["category"] or "Uncategorized", "amount": float(row["total"])}
        for row in rows
    ]
    return {"categories": categories}


@router.get("/by_tag")
def analytics_by_tag(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
):
    conditions = ["t.status = 'approved'"]
    params = []

    if date_from:
        conditions.append("t.date >= %s")
        params.append(date_from)
    if date_to:
        conditions.append("t.date <= %s")
        params.append(date_to)

    where = "WHERE " + " AND ".join(conditions)

    with db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            f"""
            SELECT tt.tag_name, SUM(t.amount) AS total
            FROM transaction_tags tt
            JOIN transactions t ON t.id = tt.transaction_id
            {where}
            GROUP BY tt.tag_name
            ORDER BY total DESC
            """,
            params,
        )
        rows = cur.fetchall()

    return {"tags": [{"name": row["tag_name"], "amount": float(row["total"])} for row in rows]}


@router.get("/trends")
def analytics_trends(
    weeks: int = Query(12, ge=1, le=52),
):
    weeks_data = []
    today = datetime.now().date()

    with db_connection() as conn:
        cur = conn.cursor()
        for week_offset in range(weeks - 1, -1, -1):
            week_end = today - timedelta(days=week_offset * 7)
            week_start = week_end - timedelta(days=6)

            cur.execute(
                """
                SELECT SUM(amount) AS total
                FROM transactions
                WHERE date >= %s AND date <= %s AND status = 'approved'
                """,
                [week_start, week_end]
            )
            row = cur.fetchone()
            total = float(row["total"]) if row["total"] else 0.0

            weeks_data.append({
                "week_start": week_start.isoformat(),
                "week_end": week_end.isoformat(),
                "total_spending": total,
            })

    return {"weeks": weeks_data}


@router.get("/by_month")
def analytics_by_month(months: int = Query(12, ge=1, le=36)):
    with db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT TO_CHAR(date, 'YYYY-MM') AS month, SUM(amount) AS total
            FROM transactions
            WHERE status = 'approved'
            GROUP BY month
            ORDER BY month DESC
            LIMIT %s
            """,
            [months],
        )
        rows = cur.fetchall()

    result = [{"month": r["month"], "total": float(r["total"])} for r in rows]
    result.reverse()
    return {"months": result}


@router.get("/by_owner")
def analytics_by_owner(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
):
    conditions = ["status = 'approved'", "owner IS NOT NULL"]
    params = []
    if date_from:
        conditions.append("date >= %s")
        params.append(date_from)
    if date_to:
        conditions.append("date <= %s")
        params.append(date_to)
    where = "WHERE " + " AND ".join(conditions)

    with db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            f"SELECT owner, SUM(amount) AS total FROM transactions {where} GROUP BY owner ORDER BY total DESC",
            params,
        )
        rows = cur.fetchall()

    return {"owners": [{"owner": r["owner"], "total": float(r["total"])} for r in rows]}


@router.get("/category_trends")
def analytics_category_trends(months: int = Query(6, ge=1, le=24)):
    with db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT TO_CHAR(date, 'YYYY-MM') AS month, category, SUM(amount) AS total
            FROM transactions
            WHERE status = 'approved' AND category IS NOT NULL
            GROUP BY month, category
            ORDER BY month ASC
            """,
        )
        rows = cur.fetchall()

    all_months = sorted({r["month"] for r in rows})
    keep_months = set(all_months[-months:])
    trends = [
        {"month": r["month"], "category": r["category"], "total": float(r["total"])}
        for r in rows if r["month"] in keep_months
    ]
    return {"trends": trends}
