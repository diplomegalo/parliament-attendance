-- Drop tables if they exist (in reverse dependency order)
DROP TABLE IF EXISTS minister_attendance CASCADE;
DROP TABLE IF EXISTS member_votes CASCADE;
DROP TABLE IF EXISTS votes CASCADE;
DROP TABLE IF EXISTS member_presences CASCADE;
DROP TABLE IF EXISTS attendance CASCADE;
DROP TABLE IF EXISTS cleaned_texts CASCADE;
DROP TABLE IF EXISTS minutes_text CASCADE;
DROP TABLE IF EXISTS minutes CASCADE;
DROP TABLE IF EXISTS sessions CASCADE;
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

-- Attendance table: Tracks member presence in sessions
CREATE TABLE IF NOT EXISTS attendance(
    id SERIAL PRIMARY KEY,
    member_id VARCHAR(50) NOT NULL,
    session_ref CHAR(4) NOT NULL,
    legislature INTEGER NOT NULL,
    spoke BOOLEAN DEFAULT FALSE,
    interventions_count INTEGER DEFAULT 0,
    confidence_score FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (member_id, legislature) 
        REFERENCES members(member_id, legislature) ON DELETE CASCADE,
    FOREIGN KEY (session_ref) 
        REFERENCES minutes(ref) ON DELETE CASCADE,
    UNIQUE(member_id, session_ref)
);

-- Indexes for attendance queries
CREATE INDEX IF NOT EXISTS idx_attendance_member 
    ON attendance(member_id, legislature);
CREATE INDEX IF NOT EXISTS idx_attendance_session 
    ON attendance(session_ref);
CREATE INDEX IF NOT EXISTS idx_attendance_spoke 
    ON attendance(spoke);

-- Votes table: Parliamentary votes by session
CREATE TABLE IF NOT EXISTS votes(
    id SERIAL PRIMARY KEY,
    session_ref CHAR(4) NOT NULL,
    vote_topic TEXT NOT NULL,
    vote_date DATE NOT NULL,
    legislature INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_ref) 
        REFERENCES minutes(ref) ON DELETE CASCADE
);

-- Indexes for vote queries
CREATE INDEX IF NOT EXISTS idx_votes_session 
    ON votes(session_ref);
CREATE INDEX IF NOT EXISTS idx_votes_date 
    ON votes(vote_date);
CREATE INDEX IF NOT EXISTS idx_votes_legislature 
    ON votes(legislature);

-- Member votes table: Individual member positions on votes
CREATE TABLE IF NOT EXISTS member_votes(
    id SERIAL PRIMARY KEY,
    vote_id INTEGER NOT NULL,
    member_id VARCHAR(50) NOT NULL,
    legislature INTEGER NOT NULL,
    position VARCHAR(20) NOT NULL CHECK (position IN ('yes', 'no', 'abstain')),
    confidence_score FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vote_id) 
        REFERENCES votes(id) ON DELETE CASCADE,
    FOREIGN KEY (member_id, legislature) 
        REFERENCES members(member_id, legislature) ON DELETE CASCADE,
    UNIQUE(vote_id, member_id)
);

-- Indexes for member vote queries
CREATE INDEX IF NOT EXISTS idx_member_votes_vote 
    ON member_votes(vote_id);
CREATE INDEX IF NOT EXISTS idx_member_votes_member 
    ON member_votes(member_id, legislature);
CREATE INDEX IF NOT EXISTS idx_member_votes_position 
    ON member_votes(position);

-- Cleaned texts table: Metadata for preprocessed text (content in storage)
CREATE TABLE IF NOT EXISTS cleaned_texts(
    id SERIAL PRIMARY KEY,
    minute_ref CHAR(4) NOT NULL UNIQUE,
    content_storage_key VARCHAR(500) NOT NULL,
    cleaning_method VARCHAR(50) NOT NULL,
    text_hash CHAR(64) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (minute_ref) 
        REFERENCES minutes(ref) ON DELETE CASCADE
);

-- Indexes for cleaned text queries
CREATE INDEX IF NOT EXISTS idx_cleaned_texts_minute_ref 
    ON cleaned_texts(minute_ref);
CREATE INDEX IF NOT EXISTS idx_cleaned_texts_text_hash 
    ON cleaned_texts(text_hash);
CREATE INDEX IF NOT EXISTS idx_cleaned_texts_cleaning_method 
    ON cleaned_texts(cleaning_method);

-- Minister attendance table: Tracks minister presence in minutes
-- Only for minutes containing vote nominatif
CREATE TABLE IF NOT EXISTS minister_attendance(
    id SERIAL PRIMARY KEY,
    minister_id VARCHAR(50) NOT NULL,
    minute_ref CHAR(4) NOT NULL,
    legislature INTEGER NOT NULL,
    present BOOLEAN NOT NULL,
    confidence_score FLOAT,
    context TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (minister_id, legislature) 
        REFERENCES members(member_id, legislature) ON DELETE CASCADE,
    FOREIGN KEY (minute_ref) 
        REFERENCES minutes(ref) ON DELETE CASCADE,
    UNIQUE(minister_id, minute_ref, legislature)
);

-- Indexes for minister attendance queries
CREATE INDEX IF NOT EXISTS idx_minister_attendance_minister 
    ON minister_attendance(minister_id, legislature);
CREATE INDEX IF NOT EXISTS idx_minister_attendance_minute 
    ON minister_attendance(minute_ref, legislature);
CREATE INDEX IF NOT EXISTS idx_minister_attendance_present 
    ON minister_attendance(present);

-- View: Minister attendance summary per minister and legislature
CREATE OR REPLACE VIEW v_minister_attendance_summary AS
SELECT 
    ma.minister_id,
    m.full_name AS minister_name,
    ma.legislature,
    COUNT(*) AS total_minutes_with_votes,
    SUM(CASE WHEN ma.present THEN 1 ELSE 0 END) AS present_count,
    SUM(CASE WHEN NOT ma.present THEN 1 ELSE 0 END) AS absent_count,
    ROUND(
        (SUM(CASE WHEN ma.present THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC) * 100, 
        2
    ) AS attendance_rate_percent,
    AVG(ma.confidence_score) AS avg_confidence_score,
    MIN(ma.created_at) AS first_record_date,
    MAX(ma.created_at) AS last_record_date
FROM 
    minister_attendance ma
JOIN 
    members m ON ma.minister_id = m.member_id AND ma.legislature = m.legislature
GROUP BY 
    ma.minister_id, m.full_name, ma.legislature
ORDER BY 
    attendance_rate_percent DESC;
