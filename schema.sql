-- RTI-Lens Database Schema

CREATE TABLE IF NOT EXISTS ministries (
    id       SERIAL PRIMARY KEY,
    name     TEXT NOT NULL UNIQUE,
    aliases  TEXT[]
);

CREATE TABLE IF NOT EXISTS cases (
    id                SERIAL PRIMARY KEY,
    order_number      TEXT UNIQUE NOT NULL,
    order_url         TEXT,
    ministry_id       INTEGER REFERENCES ministries(id),
    section_cited     TEXT,
    appeal_outcome    TEXT CHECK (appeal_outcome IN ('allowed', 'denied', 'partially_allowed')),
    appeal_level      TEXT CHECK (appeal_level IN ('first_appeal', 'second_appeal')),
    order_date        DATE,
    extraction_method TEXT CHECK (extraction_method IN ('txt', 'pdfplumber', 'ocr')),
    raw_text          TEXT,
    created_at        TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS paragraphs (
    id              SERIAL PRIMARY KEY,
    case_id         INTEGER REFERENCES cases(id) ON DELETE CASCADE,
    paragraph_index INTEGER NOT NULL,
    text            TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ministry_stats (
    ministry_id     INTEGER PRIMARY KEY REFERENCES ministries(id),
    total_orders    INTEGER,
    denied_count    INTEGER,
    allowed_count   INTEGER,
    partially_count INTEGER,
    denial_rate     FLOAT,
    override_rate   FLOAT,
    last_computed   TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS section_stats (
    section_cited     TEXT,
    ministry_id       INTEGER REFERENCES ministries(id),
    total_citations   INTEGER,
    overturned_count  INTEGER,
    misuse_rate       FLOAT,
    PRIMARY KEY (section_cited, ministry_id)
);

CREATE TABLE IF NOT EXISTS blockchain_filings (
    id                SERIAL PRIMARY KEY,
    filing_hash       TEXT NOT NULL UNIQUE,
    tx_hash           TEXT,
    block_number      INTEGER,
    applicant_name    TEXT,
    authority         TEXT,
    query_text        TEXT,
    filing_ts         TIMESTAMPTZ NOT NULL,
    deadline_ts       TIMESTAMPTZ,
    deadline_breached BOOLEAN DEFAULT FALSE,
    appeal_status     SMALLINT DEFAULT 0,
    created_at        TIMESTAMPTZ DEFAULT NOW()
);
