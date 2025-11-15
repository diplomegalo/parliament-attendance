DROP TABLE IF EXISTS minutes_text;
DROP TABLE IF EXISTS minutes;
DROP TABLE IF EXISTS members CASCADE;

CREATE TABLE IF NOT EXISTS minutes(
    id SERIAL PRIMARY KEY,
    ref CHAR(4) NOT NULL UNIQUE,
    date DATE NOT NULL,
    session VARCHAR(255) NOT NULL,
    url VARCHAR(255) NOT NULL UNIQUE,
    is_temporary BOOLEAN NOT NULL,
    content_storage_key VARCHAR(500) NOT NULL,
    legislature INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for querying by reference
CREATE INDEX IF NOT EXISTS idx_minutes_ref ON minutes(ref);

-- Index for querying by date
CREATE INDEX IF NOT EXISTS idx_minutes_date ON minutes(date);

-- Index for filtering provisional/definitive
CREATE INDEX IF NOT EXISTS idx_minutes_is_temporary ON minutes(is_temporary);

-- Index for querying by legislature
CREATE INDEX IF NOT EXISTS idx_minutes_legislature ON minutes(legislature);

-- Members table: Official list of parliament members
CREATE TABLE IF NOT EXISTS members(
    id SERIAL PRIMARY KEY,
    member_id VARCHAR(50) NOT NULL,
    legislature INTEGER NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    first_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(member_id, legislature)
);

-- Index for name lookups (fuzzy matching)
CREATE INDEX IF NOT EXISTS idx_members_full_name 
    ON members(full_name);
CREATE INDEX IF NOT EXISTS idx_members_last_name 
    ON members(last_name);
CREATE INDEX IF NOT EXISTS idx_members_legislature 
    ON members(legislature);

-- Full text search index for member names
CREATE INDEX IF NOT EXISTS idx_members_name_search 
    ON members USING gin(to_tsvector('simple', 
        full_name || ' ' || last_name || ' ' || first_name));

