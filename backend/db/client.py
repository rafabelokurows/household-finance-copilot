"""SQLite connection and schema initialization."""
import os
import sqlite3
import uuid
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

_DB_PATH = os.getenv("DB_PATH", "data/finance.db")
_SCHEMA_PATH = Path(__file__).parent / "schema.sql"
_conn: sqlite3.Connection | None = None


def get_connection() -> sqlite3.Connection:
    """Return (or create) the singleton SQLite connection."""
    global _conn
    if _conn is None:
        Path(_DB_PATH).parent.mkdir(parents=True, exist_ok=True)
        _conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA foreign_keys = ON")
        _initialize_schema(_conn)
    return _conn


def _initialize_schema(conn: sqlite3.Connection) -> None:
    schema_sql = _SCHEMA_PATH.read_text()
    for statement in schema_sql.split(';'):
        if statement.strip():
            conn.execute(statement)
    conn.commit()
    _seed_category_rules(conn)


def _seed_category_rules(conn: sqlite3.Connection) -> None:
    """Seed category_rules table from hardcoded RULES if table is empty."""
    count = conn.execute("SELECT COUNT(*) FROM category_rules").fetchone()[0]
    if count > 0:
        return
    from ..ingestion.category_rules import RULES
    priority = 0
    for keywords, category in RULES:
        for keyword in keywords:
            conn.execute(
                "INSERT OR IGNORE INTO category_rules (category, keyword, priority) VALUES (?, ?, ?)",
                [category, keyword, priority],
            )
            priority += 1
    conn.commit()
    import logging
    logging.getLogger(__name__).info("Seeded %d category rules", priority)


def generate_id() -> str:
    return str(uuid.uuid4())
