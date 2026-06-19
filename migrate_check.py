import sqlite3, psycopg2, os
from dotenv import load_dotenv

load_dotenv('backend/.env')

src = sqlite3.connect('data/finance.db')
src.row_factory = sqlite3.Row
dst = psycopg2.connect(os.environ['DATABASE_URL'])

tables = [r[0] for r in src.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print('Tables found:', tables)

for t in tables:
    count = src.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(f"  {t}: {count} rows")

src.close()
dst.close()
