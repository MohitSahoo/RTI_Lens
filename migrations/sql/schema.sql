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
    ministry_id       INTEGER NOT NULL REFERENCES ministries(id) ON DELETE RESTRICT,
    section_cited     TEXT,
    appeal_outcome    TEXT CHECK (appeal_outcome IN ('allowed', 'denied', 'partially_allowed')),
    appeal_level      TEXT CHECK (appeal_level IN ('first_appeal', 'second_appeal')),
    order_date        DATE,
    extraction_method TEXT NOT NULL CHECK (extraction_method IN ('txt', 'pdfplumber', 'ocr')),
    raw_text          TEXT NOT NULL CHECK (raw_text <> ''),
    created_at        TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT check_case_order_number_not_blank CHECK (length(trim(order_number)) > 0)
);

CREATE TABLE IF NOT EXISTS paragraphs (
    id              SERIAL PRIMARY KEY,
    case_id         INTEGER NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    paragraph_index INTEGER NOT NULL,
    text            TEXT NOT NULL CHECK (text <> ''),
    CONSTRAINT uq_paragraph_case_index UNIQUE (case_id, paragraph_index),
    CONSTRAINT check_paragraph_index_non_negative CHECK (paragraph_index >= 0)
);

CREATE TABLE IF NOT EXISTS ministry_stats (
    ministry_id     INTEGER PRIMARY KEY REFERENCES ministries(id),
    total_orders    INTEGER,
    denied_count    INTEGER,
    allowed_count   INTEGER,
    partially_count INTEGER,
    denial_rate     FLOAT,
    override_rate   FLOAT,
    last_computed   TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT check_ministry_stats_total_orders_non_negative CHECK (total_orders IS NULL OR total_orders >= 0),
    CONSTRAINT check_ministry_stats_denied_count_non_negative CHECK (denied_count IS NULL OR denied_count >= 0),
    CONSTRAINT check_ministry_stats_allowed_count_non_negative CHECK (allowed_count IS NULL OR allowed_count >= 0),
    CONSTRAINT check_ministry_stats_partially_count_non_negative CHECK (partially_count IS NULL OR partially_count >= 0),
    CONSTRAINT check_ministry_stats_denial_rate_range CHECK (denial_rate IS NULL OR (denial_rate >= 0 AND denial_rate <= 1)),
    CONSTRAINT check_ministry_stats_override_rate_range CHECK (override_rate IS NULL OR (override_rate >= 0 AND override_rate <= 1))
);

CREATE TABLE IF NOT EXISTS section_stats (
    section_cited     TEXT,
    ministry_id       INTEGER REFERENCES ministries(id),
    total_citations   INTEGER,
    overturned_count  INTEGER,
    misuse_rate       FLOAT,
    PRIMARY KEY (section_cited, ministry_id),
    CONSTRAINT check_section_stats_total_citations_non_negative CHECK (total_citations IS NULL OR total_citations >= 0),
    CONSTRAINT check_section_stats_overturned_count_non_negative CHECK (overturned_count IS NULL OR overturned_count >= 0),
    CONSTRAINT check_section_stats_misuse_rate_range CHECK (misuse_rate IS NULL OR (misuse_rate >= 0 AND misuse_rate <= 1))
);

CREATE TABLE IF NOT EXISTS blockchain_filings (
    id                SERIAL PRIMARY KEY,
    filing_hash       TEXT NOT NULL UNIQUE,
    tx_hash           TEXT,
    block_number      INTEGER,
    applicant_name    TEXT NOT NULL,
    authority         TEXT NOT NULL,
    query_text        TEXT NOT NULL,
    filing_ts         TIMESTAMPTZ NOT NULL,
    deadline_ts       TIMESTAMPTZ,
    deadline_breached BOOLEAN DEFAULT FALSE,
    appeal_status     SMALLINT DEFAULT 0,
    created_at        TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT check_blockchain_filing_hash_not_blank CHECK (length(trim(filing_hash)) > 0),
    CONSTRAINT check_blockchain_applicant_name_not_blank CHECK (length(trim(applicant_name)) > 0),
    CONSTRAINT check_blockchain_authority_not_blank CHECK (length(trim(authority)) > 0),
    CONSTRAINT check_blockchain_query_text_not_blank CHECK (length(trim(query_text)) > 0),
    CONSTRAINT check_blockchain_block_number_non_negative CHECK (block_number IS NULL OR block_number >= 0),
    CONSTRAINT check_blockchain_appeal_status CHECK (appeal_status IN (0, 1, 2)),
    CONSTRAINT check_blockchain_deadline_after_filing CHECK (deadline_ts IS NULL OR deadline_ts >= filing_ts)
);
