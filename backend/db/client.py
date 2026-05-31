"""DuckDB connection and schema initialization."""
import os
import uuid
from pathlib import Path
import duckdb
from dotenv import load_dotenv

load_dotenv()

_DUCKDB_PATH = os.getenv("DUCKDB_PATH", "data/finance.duckdb")
_SCHEMA_PATH = Path(__file__).parent / "schema.sql"
_conn: duckdb.DuckDBPyConnection | None = None


def get_connection() -> duckdb.DuckDBPyConnection:
    """Return (or create) the singleton DuckDB connection."""
    global _conn
    if _conn is None:
        Path(_DUCKDB_PATH).parent.mkdir(parents=True, exist_ok=True)
        _conn = duckdb.connect(_DUCKDB_PATH)
        _initialize_schema(_conn)
    return _conn


def _initialize_schema(conn: duckdb.DuckDBPyConnection) -> None:
    schema_sql = _SCHEMA_PATH.read_text()
    conn.execute(schema_sql)


def generate_id() -> str:
    return str(uuid.uuid4())
