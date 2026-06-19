import sqlite3
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv('backend/.env')

src = sqlite3.connect('data/finance.db')
src.row_factory = sqlite3.Row
dst = psycopg2.connect(os.environ['DATABASE_URL'])
cur = dst.cursor()

# Schema
cur.execute(open('backend/db/schema.sql').read())
dst.commit()
print("Schema created.")

def migrate_table(table, rows, insert_sql):
    if not rows:
        print(f"  {table}: 0 rows, skip")
        return
    cur.executemany(insert_sql, [tuple(r) for r in rows])
    dst.commit()
    print(f"  {table}: {len(rows)} rows migrated")

# transactions
rows = src.execute("SELECT id, date, merchant, amount, currency, category, owner, confidence, status, source_file, bank, description, raw_json, created_at FROM transactions").fetchall()
migrate_table("transactions", rows, """
    INSERT INTO transactions (id, date, merchant, amount, currency, category, owner, confidence, status, source_file, bank, description, raw_json, created_at)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (id) DO NOTHING
""")

# tags
rows = src.execute("SELECT name FROM tags").fetchall()
migrate_table("tags", rows, "INSERT INTO tags (name) VALUES (%s) ON CONFLICT DO NOTHING")

# transaction_tags (only where transaction exists)
rows = src.execute("""
    SELECT tt.transaction_id, tt.tag_name FROM transaction_tags tt
    WHERE EXISTS (SELECT 1 FROM transactions t WHERE t.id = tt.transaction_id)
""").fetchall()
migrate_table("transaction_tags", rows, "INSERT INTO transaction_tags (transaction_id, tag_name) VALUES (%s, %s) ON CONFLICT DO NOTHING")

# category_rules
rows = src.execute("SELECT category, keyword, priority FROM category_rules").fetchall()
migrate_table("category_rules", rows, "INSERT INTO category_rules (category, keyword, priority) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING")

# gmail_poll_state
rows = src.execute("SELECT key, value FROM gmail_poll_state").fetchall()
migrate_table("gmail_poll_state", rows, "INSERT INTO gmail_poll_state (key, value) VALUES (%s, %s) ON CONFLICT DO NOTHING")

# gmail_processed_messages
rows = src.execute("SELECT message_id, processed_at FROM gmail_processed_messages").fetchall()
migrate_table("gmail_processed_messages", rows, "INSERT INTO gmail_processed_messages (message_id, processed_at) VALUES (%s, %s) ON CONFLICT DO NOTHING")

# processed_attachments
rows = src.execute("SELECT content_hash, filename, processed_at FROM processed_attachments").fetchall()
migrate_table("processed_attachments", rows, "INSERT INTO processed_attachments (content_hash, filename, processed_at) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING")

src.close()
dst.close()
print("Done.")
