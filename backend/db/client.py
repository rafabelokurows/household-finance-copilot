"""SQLite connection and schema initialization."""
import os
import sqlite3
import uuid
from pathlib import Path
from datetime import datetime
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
    _seed_data(conn)


def _seed_data(conn: sqlite3.Connection) -> None:
    """Seed test data if table is empty."""
    # Check if we already have data
    count = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
    if count > 0:
        return

    # Insert test transactions
    test_transactions = [
        ("2024-06-01", "Carrefour", 45.50, "EUR", "Groceries", "Rafael", 0.85, "pending", None, "Supermarket"),
        ("2024-06-02", "Nespresso", 12.99, "EUR", "Other", "Heloisa", 0.90, "pending", None, "Coffee"),
        ("2024-06-02", "SNCF", 89.00, "EUR", "Transportation", "Shared", 0.95, "pending", None, "Train ticket"),
        ("2024-06-03", "Netflix", 15.99, "EUR", "Entertainment", "Shared", 0.99, "approved", None, "Streaming"),
        ("2024-06-03", "Pharmacie", 23.45, "EUR", "Healthcare", "Rafael", 0.92, "approved", None, "Pharmacy"),
        ("2024-06-04", "Amazon", 67.89, "EUR", "Shopping", "Heloisa", 0.88, "approved", None, "Online shopping"),
        ("2024-06-04", "Restaurant Le Petit", 52.30, "EUR", "Dining", "Shared", 0.87, "pending", None, "Dinner"),
        ("2024-06-05", "EDF", 98.50, "EUR", "Utilities", "Shared", 0.99, "approved", None, "Electricity bill"),
        ("2024-06-05", "Ikea", 189.00, "EUR", "Shopping", "Shared", 0.91, "pending", None, "Furniture"),
        ("2024-06-06", "Uber", 18.75, "EUR", "Transportation", "Rafael", 0.94, "pending", None, "Ride"),
    ]

    first_tx_id = None
    for date, merchant, amount, currency, category, owner, confidence, status, bank, desc in test_transactions:
        tx_id = generate_id()
        if first_tx_id is None:
            first_tx_id = tx_id
        conn.execute(
            """INSERT INTO transactions
            (id, date, merchant, amount, currency, category, owner, confidence, status, bank, description, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [tx_id, date, merchant, amount, currency, category, owner, confidence, status, bank, desc, datetime.now().isoformat()]
        )

    # Seed one test document (minimal valid 1x1 white PNG)
    if first_tx_id:
        _minimal_png = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
            b'\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00'
            b'\x00\x0cIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfe\xdc'
            b'\xccY\xe7\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        conn.execute(
            """INSERT INTO documents (id, transaction_id, filename, mime_type, file_blob, uploaded_at)
            VALUES (?, ?, ?, ?, ?, ?)""",
            [generate_id(), first_tx_id, "test-receipt.png", "image/png", _minimal_png, datetime.now().isoformat()]
        )

    conn.commit()


def generate_id() -> str:
    return str(uuid.uuid4())
