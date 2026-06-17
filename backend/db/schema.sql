CREATE TABLE IF NOT EXISTS transactions (
    id          TEXT PRIMARY KEY,
    date        DATE NOT NULL,
    merchant    TEXT NOT NULL,
    amount      DECIMAL(12,2) NOT NULL,
    currency    TEXT DEFAULT 'EUR',
    category    TEXT,
    owner       TEXT CHECK (owner IN ('Rafael','Heloisa','Shared')),
    confidence  DECIMAL(5,4) NOT NULL DEFAULT 0.5,
    status      TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','approved','rejected')),
    source_file TEXT,
    bank        TEXT,
    description TEXT,
    raw_json    TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS documents (
    id             TEXT PRIMARY KEY,
    transaction_id TEXT NOT NULL,
    filename       TEXT NOT NULL,
    mime_type      TEXT NOT NULL DEFAULT 'application/octet-stream',
    file_blob      BYTEA NOT NULL,
    uploaded_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
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
);

CREATE TABLE IF NOT EXISTS processed_attachments (
    content_hash TEXT PRIMARY KEY,
    filename     TEXT NOT NULL,
    processed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS category_rules (
    id       SERIAL PRIMARY KEY,
    category TEXT NOT NULL,
    keyword  TEXT NOT NULL,
    priority INTEGER NOT NULL,
    UNIQUE(category, keyword)
);
