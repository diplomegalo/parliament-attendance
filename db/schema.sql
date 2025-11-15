DROP TABLE IF EXISTS minutes_text;
DROP TABLE IF EXISTS minutes;

CREATE TABLE IF NOT EXISTS minutes(
    id SERIAL PRIMARY KEY,
    ref CHAR(4) NOT NULL UNIQUE,
    date DATE NOT NULL,
    session VARCHAR(255) NOT NULL,
    url VARCHAR(255) NOT NULL UNIQUE,
    is_temporary BOOLEAN NOT NULL,
    content_storage_key VARCHAR(500) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for querying by reference
CREATE INDEX IF NOT EXISTS idx_minutes_ref ON minutes(ref);

-- Index for querying by date
CREATE INDEX IF NOT EXISTS idx_minutes_date ON minutes(date);

-- Index for filtering provisional/definitive
CREATE INDEX IF NOT EXISTS idx_minutes_is_temporary ON minutes(is_temporary);
