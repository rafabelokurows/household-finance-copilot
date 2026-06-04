CREATE TABLE IF NOT EXISTS transactions (
    id          TEXT PRIMARY KEY,
    date        DATE NOT NULL,
    merchant    TEXT NOT NULL,
    amount      REAL NOT NULL,
    currency    TEXT DEFAULT 'EUR',
    category    TEXT,
    owner       TEXT CHECK (owner IN ('Rafael','Heloisa','Shared')),
    confidence  REAL NOT NULL DEFAULT 0.5,
    status      TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','approved','rejected')),
    source_file TEXT,
    bank        TEXT,
    description TEXT,
    raw_json    TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS documents (
    id             TEXT PRIMARY KEY,
    transaction_id TEXT NOT NULL,
    filename       TEXT NOT NULL,
    mime_type      TEXT NOT NULL DEFAULT 'application/octet-stream',
    file_blob      BLOB NOT NULL,
    uploaded_at    TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (transaction_id) REFERENCES transactions(id)
);

CREATE TABLE IF NOT EXISTS tags (
    name TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS transaction_tags (
    transaction_id TEXT NOT NULL,
    tag_name       TEXT NOT NULL,
    PRIMARY KEY (transaction_id, tag_name),
    FOREIGN KEY (transaction_id) REFERENCES transactions(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_name) REFERENCES tags(name)
);

CREATE TABLE IF NOT EXISTS gmail_poll_state (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS gmail_processed_messages (
    message_id   TEXT PRIMARY KEY,
    processed_at TEXT NOT NULL
)
