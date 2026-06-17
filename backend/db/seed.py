"""One-time seed script: populate category_rules in Supabase.

Usage:
    DATABASE_URL=postgresql://... python -m backend.db.seed
"""
import logging
from .client import db_connection
from ..ingestion.category_rules import RULES

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def seed_category_rules() -> None:
    with db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM category_rules")
        row = cur.fetchone()
        if row["count"] > 0:
            log.info("category_rules already seeded (%d rows), skipping", row["count"])
            return
        priority = 0
        for keywords, category in RULES:
            for keyword in keywords:
                cur.execute(
                    "INSERT INTO category_rules (category, keyword, priority) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
                    [category, keyword, priority],
                )
                priority += 1
        conn.commit()
        log.info("Seeded %d category rules", priority)


if __name__ == "__main__":
    seed_category_rules()
