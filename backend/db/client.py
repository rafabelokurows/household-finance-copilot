"""Postgres connection pool via psycopg2."""
import os
import uuid
from contextlib import contextmanager

from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import RealDictCursor
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

_pool: ThreadedConnectionPool | None = None


def _get_pool() -> ThreadedConnectionPool:
    global _pool
    if _pool is None:
        _pool = ThreadedConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=os.environ["DATABASE_URL"],
            cursor_factory=RealDictCursor,
        )
    return _pool


def get_connection():
    return _get_pool().getconn()


def release_connection(conn) -> None:
    _get_pool().putconn(conn)


@contextmanager
def db_connection():
    conn = get_connection()
    try:
        yield conn
    except Exception:
        conn.rollback()
        raise
    finally:
        release_connection(conn)


def generate_id() -> str:
    return str(uuid.uuid4())
