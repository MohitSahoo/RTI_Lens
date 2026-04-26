
-- RTI-Lens schema hardening migration
-- Date: 2026-04-26
--
-- Purpose:
-- 1. Align the live PostgreSQL schema with the tightened SQLAlchemy models.
-- 2. Enforce non-nullable and content constraints added in Phase A/B hardening.
-- 3. Preserve text storage for enum-backed application fields while tightening
--    allowed values with database CHECK constraints.
--
-- Important:
-- - The ORM now uses SQLAlchemy enums with native_enum=False for:
--   cases.appeal_outcome, cases.appeal_level, cases.extraction_method
-- - In PostgreSQL these remain TEXT columns. No CREATE TYPE is required.
-- - This migration is intended to fail fast if existing data violates the new rules.

BEGIN;

-- ============================================================================
-- Preflight validation
-- ============================================================================

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM cases WHERE ministry_id IS NULL) THEN
        RAISE EXCEPTION 'Migration blocked: cases.ministry_id contains NULL values. Backfill ministry mappings before applying NOT NULL.';
    END IF;

    IF EXISTS (SELECT 1 FROM cases WHERE raw_text IS NULL OR raw_text = '') THEN
        RAISE EXCEPTION 'Migration blocked: cases.raw_text contains NULL/empty values.';
    END IF;

    IF EXISTS (SELECT 1 FROM cases WHERE extraction_method IS NULL) THEN
        RAISE EXCEPTION 'Migration blocked: cases.extraction_method contains NULL values.';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM paragraphs
        GROUP BY case_id, paragraph_index
        HAVING COUNT(*) > 1
    ) THEN
        RAISE EXCEPTION 'Migration blocked: duplicate (case_id, paragraph_index) rows exist in paragraphs.';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM blockchain_filings
        WHERE applicant_name IS NULL
           OR authority IS NULL
           OR query_text IS NULL
           OR trim(filing_hash) = ''
           OR trim(applicant_name) = ''
           OR trim(authority) = ''
           OR trim(query_text) = ''
           OR (block_number IS NOT NULL AND block_number < 0)
           OR appeal_status NOT IN (0, 1, 2)
           OR (deadline_ts IS NOT NULL AND deadline_ts < filing_ts)
    ) THEN
        RAISE EXCEPTION 'Migration blocked: blockchain_filings contains rows that violate the new hardening constraints.';
    END IF;
END $$;

-- ============================================================================
-- cases
-- ============================================================================

ALTER TABLE cases
    ALTER COLUMN ministry_id SET NOT NULL,
    ALTER COLUMN extraction_method SET NOT NULL,
    ALTER COLUMN raw_text SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'check_case_order_number_not_blank'
    ) THEN
        ALTER TABLE cases
            ADD CONSTRAINT check_case_order_number_not_blank
            CHECK (length(trim(order_number)) > 0);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'check_case_raw_text_not_empty'
    ) THEN
        ALTER TABLE cases
            ADD CONSTRAINT check_case_raw_text_not_empty
            CHECK (raw_text <> '');
    END IF;
END $$;

-- Application enums are persisted as TEXT, constrained at the DB layer.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'check_appeal_outcome'
    ) THEN
        ALTER TABLE cases
            ADD CONSTRAINT check_appeal_outcome
            CHECK (appeal_outcome IN ('allowed', 'denied', 'partially_allowed'));
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'check_appeal_level'
    ) THEN
        ALTER TABLE cases
            ADD CONSTRAINT check_appeal_level
            CHECK (appeal_level IN ('first_appeal', 'second_appeal'));
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'check_extraction_method'
    ) THEN
        ALTER TABLE cases
            ADD CONSTRAINT check_extraction_method
            CHECK (extraction_method IN ('txt', 'pdfplumber', 'ocr'));
    END IF;
END $$;

-- ============================================================================
-- paragraphs
-- ============================================================================

ALTER TABLE paragraphs
    ALTER COLUMN case_id SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'uq_paragraph_case_index'
    ) THEN
        ALTER TABLE paragraphs
            ADD CONSTRAINT uq_paragraph_case_index
            UNIQUE (case_id, paragraph_index);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'check_paragraph_index_non_negative'
    ) THEN
        ALTER TABLE paragraphs
            ADD CONSTRAINT check_paragraph_index_non_negative
            CHECK (paragraph_index >= 0);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'check_paragraph_text_not_empty'
    ) THEN
        ALTER TABLE paragraphs
            ADD CONSTRAINT check_paragraph_text_not_empty
            CHECK (text <> '');
    END IF;
END $$;

-- ============================================================================
-- ministry_stats
-- ============================================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'check_ministry_stats_total_orders_non_negative'
    ) THEN
        ALTER TABLE ministry_stats
            ADD CONSTRAINT check_ministry_stats_total_orders_non_negative
            CHECK (total_orders IS NULL OR total_orders >= 0);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'check_ministry_stats_denied_count_non_negative'
    ) THEN
        ALTER TABLE ministry_stats
            ADD CONSTRAINT check_ministry_stats_denied_count_non_negative
            CHECK (denied_count IS NULL OR denied_count >= 0);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'check_ministry_stats_allowed_count_non_negative'
    ) THEN
        ALTER TABLE ministry_stats
            ADD CONSTRAINT check_ministry_stats_allowed_count_non_negative
            CHECK (allowed_count IS NULL OR allowed_count >= 0);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'check_ministry_stats_partially_count_non_negative'
    ) THEN
        ALTER TABLE ministry_stats
            ADD CONSTRAINT check_ministry_stats_partially_count_non_negative
            CHECK (partially_count IS NULL OR partially_count >= 0);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'check_ministry_stats_denial_rate_range'
    ) THEN
        ALTER TABLE ministry_stats
            ADD CONSTRAINT check_ministry_stats_denial_rate_range
            CHECK (denial_rate IS NULL OR (denial_rate >= 0 AND denial_rate <= 1));
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'check_ministry_stats_override_rate_range'
    ) THEN
        ALTER TABLE ministry_stats
            ADD CONSTRAINT check_ministry_stats_override_rate_range
            CHECK (override_rate IS NULL OR (override_rate >= 0 AND override_rate <= 1));
    END IF;
END $$;

-- ============================================================================
-- section_stats
-- ============================================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'check_section_stats_total_citations_non_negative'
    ) THEN
        ALTER TABLE section_stats
            ADD CONSTRAINT check_section_stats_total_citations_non_negative
            CHECK (total_citations IS NULL OR total_citations >= 0);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'check_section_stats_overturned_count_non_negative'
    ) THEN
        ALTER TABLE section_stats
            ADD CONSTRAINT check_section_stats_overturned_count_non_negative
            CHECK (overturned_count IS NULL OR overturned_count >= 0);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'check_section_stats_misuse_rate_range'
    ) THEN
        ALTER TABLE section_stats
            ADD CONSTRAINT check_section_stats_misuse_rate_range
            CHECK (misuse_rate IS NULL OR (misuse_rate >= 0 AND misuse_rate <= 1));
    END IF;
END $$;

-- ============================================================================
-- blockchain_filings
-- ============================================================================

ALTER TABLE blockchain_filings
    ALTER COLUMN applicant_name SET NOT NULL,
    ALTER COLUMN authority SET NOT NULL,
    ALTER COLUMN query_text SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'check_blockchain_filing_hash_not_blank'
    ) THEN
        ALTER TABLE blockchain_filings
            ADD CONSTRAINT check_blockchain_filing_hash_not_blank
            CHECK (length(trim(filing_hash)) > 0);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'check_blockchain_applicant_name_not_blank'
    ) THEN
        ALTER TABLE blockchain_filings
            ADD CONSTRAINT check_blockchain_applicant_name_not_blank
            CHECK (length(trim(applicant_name)) > 0);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'check_blockchain_authority_not_blank'
    ) THEN
        ALTER TABLE blockchain_filings
            ADD CONSTRAINT check_blockchain_authority_not_blank
            CHECK (length(trim(authority)) > 0);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'check_blockchain_query_text_not_blank'
    ) THEN
        ALTER TABLE blockchain_filings
            ADD CONSTRAINT check_blockchain_query_text_not_blank
            CHECK (length(trim(query_text)) > 0);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'check_blockchain_block_number_non_negative'
    ) THEN
        ALTER TABLE blockchain_filings
            ADD CONSTRAINT check_blockchain_block_number_non_negative
            CHECK (block_number IS NULL OR block_number >= 0);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'check_blockchain_appeal_status'
    ) THEN
        ALTER TABLE blockchain_filings
            ADD CONSTRAINT check_blockchain_appeal_status
            CHECK (appeal_status IN (0, 1, 2));
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'check_blockchain_deadline_after_filing'
    ) THEN
        ALTER TABLE blockchain_filings
            ADD CONSTRAINT check_blockchain_deadline_after_filing
            CHECK (deadline_ts IS NULL OR deadline_ts >= filing_ts);
    END IF;
END $$;

COMMIT;
