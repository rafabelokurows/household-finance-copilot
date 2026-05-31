CREATE TABLE IF NOT EXISTS transactions (
    id          VARCHAR PRIMARY KEY,
    date        DATE NOT NULL,
    merchant    VARCHAR NOT NULL,
    amount      DECIMAL(12,2) NOT NULL,
    currency    VARCHAR DEFAULT 'EUR',
    category    VARCHAR,
    owner       VARCHAR CHECK (owner IN ('Rafael','Heloisa','Shared')),
    confidence  FLOAT NOT NULL DEFAULT 0.5,
    status      VARCHAR NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','approved','rejected')),
    source_file VARCHAR,
    bank        VARCHAR,
    raw_json    JSON,
    created_at  TIMESTAMP DEFAULT now()
);
