"""
Populates ministry_stats and section_stats tables from the cases table.
Run after ingestion completes.
"""

from sqlalchemy import create_engine, text

DB_URL = "postgresql://mohitsahoo@localhost:5432/rtilens"
engine = create_engine(DB_URL)

with engine.begin() as conn:
    # ministry_stats
    conn.execute(text("DELETE FROM ministry_stats"))
    conn.execute(text("""
        INSERT INTO ministry_stats
          (ministry_id, total_orders, denied_count, allowed_count,
           partially_count, denial_rate, override_rate)
        SELECT
          ministry_id,
          COUNT(*) AS total_orders,
          SUM(CASE WHEN appeal_outcome = 'denied' THEN 1 ELSE 0 END) AS denied_count,
          SUM(CASE WHEN appeal_outcome = 'allowed' THEN 1 ELSE 0 END) AS allowed_count,
          SUM(CASE WHEN appeal_outcome = 'partially_allowed' THEN 1 ELSE 0 END) AS partially_count,
          ROUND(
            SUM(CASE WHEN appeal_outcome = 'denied' THEN 1 ELSE 0 END)::NUMERIC / COUNT(*), 4
          ) AS denial_rate,
          ROUND(
            SUM(CASE WHEN appeal_outcome = 'allowed' THEN 1 ELSE 0 END)::NUMERIC / NULLIF(
              SUM(CASE WHEN appeal_outcome IN ('allowed', 'denied') THEN 1 ELSE 0 END), 0
            ), 4
          ) AS override_rate
        FROM cases
        WHERE ministry_id IS NOT NULL
          AND appeal_outcome IS NOT NULL
        GROUP BY ministry_id
        HAVING COUNT(*) >= 5
    """))

    # section_stats
    conn.execute(text("DELETE FROM section_stats"))
    conn.execute(text("""
        INSERT INTO section_stats
          (section_cited, ministry_id, total_citations, overturned_count, misuse_rate)
        SELECT
          section_cited,
          ministry_id,
          COUNT(*) AS total_citations,
          SUM(CASE WHEN appeal_outcome = 'allowed' THEN 1 ELSE 0 END) AS overturned_count,
          ROUND(
            SUM(CASE WHEN appeal_outcome = 'allowed' THEN 1 ELSE 0 END)::NUMERIC / COUNT(*), 4
          ) AS misuse_rate
        FROM cases
        WHERE section_cited IS NOT NULL
          AND ministry_id IS NOT NULL
          AND appeal_outcome IS NOT NULL
        GROUP BY section_cited, ministry_id
    """))

print("Stats computed successfully.")
