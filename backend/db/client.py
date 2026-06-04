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
    # SQLite doesn't support multiple statements in one execute, so split them
    for statement in schema_sql.split(';'):
        if statement.strip():
            conn.execute(statement)
    conn.commit()


def generate_id() -> str:
    return str(uuid.uuid4())
