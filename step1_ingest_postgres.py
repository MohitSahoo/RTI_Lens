#!/usr/bin/env python3
"""
Step 1: PostgreSQL Ingestion Only
Ingest JSONL to PostgreSQL database
"""

import json
import sys
from pathlib import Path
from sqlalchemy import create_engine, text
from tqdm import tqdm

JSONL_FILE = Path("clean_cases_final_balanced.jsonl")
POSTGRES_URL = "postgresql://mohitsahoo@localhost:5432/rtilens"

print("="*60)
print("STEP 1: PostgreSQL Ingestion")
print("="*60)

# Connect
engine = create_engine(POSTGRES_URL)
conn = engine.connect()

# Clean
print("\nCleaning PostgreSQL tables...")
tables = ['workflow_actions', 'workflow_sessions', 'paragraphs', 'section_stats', 'ministry_stats', 'cases', 'ministries']
for table in tables:
    try:
        conn.execute(text(f'DELETE FROM {table}'))
        conn.commit()
        print(f"  ✓ Cleared {table}")
    except:
        pass

# Load JSONL
print(f"\nLoading {JSONL_FILE}...")
with open(JSONL_FILE, 'r', encoding='utf-8') as f:
    cases = [json.loads(line) for line in f]

print(f"Found {len(cases)} cases")

# Ministry cache
ministry_cache = {}

def get_or_create_ministry(name):
    if not name or name == "Unknown":
        name = "Unknown Ministry"

    if name in ministry_cache:
        return ministry_cache[name]

    result = conn.execute(
        text("SELECT id FROM ministries WHERE name = :name"),
        {"name": name}
    ).fetchone()

    if result:
        ministry_id = result[0]
    else:
        ministry_id = conn.execute(
            text("INSERT INTO ministries (name) VALUES (:name) RETURNING id"),
            {"name": name}
        ).fetchone()[0]
        conn.commit()

    ministry_cache[name] = ministry_id
    return ministry_id

# Ingest cases
print("\nIngesting cases to PostgreSQL...")
for case in tqdm(cases, desc="Processing"):
    metadata = case.get('metadata', {})
    order_number = metadata.get('order_number', case.get('case_id', 'unknown'))
    ministry_id = get_or_create_ministry(metadata.get('ministry'))
    raw_text = case.get('clean_text') or case.get('raw_text', '')

    # Insert case
    result = conn.execute(
        text("""
            INSERT INTO cases (
                order_number, ministry_id, section_cited,
                appeal_outcome, appeal_level, order_date,
                extraction_method, raw_text
            ) VALUES (
                :order_number, :ministry_id, :section_cited,
                :appeal_outcome, :appeal_level, :order_date,
                'jsonl', :raw_text
            ) RETURNING id
        """),
        {
            "order_number": order_number,
            "ministry_id": ministry_id,
            "section_cited": metadata.get('section_cited'),
            "appeal_outcome": metadata.get('appeal_outcome'),
            "appeal_level": metadata.get('appeal_level'),
            "order_date": None,
            "raw_text": raw_text
        }
    )
    case_id = result.fetchone()[0]

    # Insert paragraphs
    paragraphs = case.get('paragraphs', [])
    if isinstance(paragraphs, list):
        for idx, para in enumerate(paragraphs):
            if isinstance(para, str) and para.strip():
                conn.execute(
                    text("INSERT INTO paragraphs (case_id, paragraph_index, text) VALUES (:cid, :idx, :text)"),
                    {"cid": case_id, "idx": idx, "text": para.strip()}
                )

    conn.commit()

# Verify
case_count = conn.execute(text("SELECT COUNT(*) FROM cases")).scalar()
para_count = conn.execute(text("SELECT COUNT(*) FROM paragraphs")).scalar()
ministry_count = conn.execute(text("SELECT COUNT(*) FROM ministries")).scalar()

print("\n" + "="*60)
print("STEP 1 COMPLETE")
print("="*60)
print(f"✓ Cases: {case_count}")
print(f"✓ Paragraphs: {para_count}")
print(f"✓ Ministries: {ministry_count}")

conn.close()
engine.dispose()
