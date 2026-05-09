#!/usr/bin/env python3
"""
Step 4: Build BM25 Index
Creates BM25 index from PostgreSQL paragraphs
"""

import pickle
from pathlib import Path
from sqlalchemy import create_engine, text
from rank_bm25 import BM25Okapi
import re

POSTGRES_URL = "postgresql://mohitsahoo@localhost:5432/rtilens"
OUT_PATH = Path("data/bm25_pageindex.pkl")

print("="*60)
print("STEP 4: Build BM25 Index")
print("="*60)

# Tokenizer
STOPWORDS = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been', 'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'what', 'which', 'who', 'when', 'where', 'why', 'how'}

def tokenize(text):
    text = text.lower()
    section_pattern = re.compile(r'\b\d+\(?[\w\d]*\)?(?:\(?[\w\d]*\)?)*\b')
    sections = section_pattern.findall(text)
    clean_text = re.sub(r'[^a-z0-9\(\)\[\]]', ' ', text)
    tokens = clean_text.split()

    result = []
    for t in tokens:
        if t in sections or section_pattern.match(t):
            result.append(t)
            continue
        t_word = t.strip('()[]')
        if len(t_word) > 1 and t_word.isalnum() and t_word not in STOPWORDS:
            result.append(t_word)

    return list(set(result))

# Connect to database
engine = create_engine(POSTGRES_URL)

print("\nLoading paragraphs from PostgreSQL...")
with engine.connect() as conn:
    rows = conn.execute(text("""
        SELECT p.id, p.case_id, p.paragraph_index, p.text,
               c.order_number, c.order_date,
               m.name AS ministry
        FROM paragraphs p
        JOIN cases c ON c.id = p.case_id
        LEFT JOIN ministries m ON m.id = c.ministry_id
        ORDER BY p.id
    """)).fetchall()

print(f"Loaded {len(rows)} paragraphs")

if len(rows) == 0:
    print("ERROR: No paragraphs found. Run Step 1 first.")
    sys.exit(1)

print("\nTokenizing...")
corpus_tokens = []
page_index = []

for row in rows:
    tokens = tokenize(row.text)
    corpus_tokens.append(tokens)
    page_index.append({
        "paragraph_id": row.id,
        "case_id": row.case_id,
        "order_number": row.order_number,
        "ministry": row.ministry or "Unknown",
        "order_date": str(row.order_date) if row.order_date else None,
        "paragraph_index": row.paragraph_index,
        "text": row.text,
    })

print("Building BM25 index...")
bm25 = BM25Okapi(corpus_tokens)

print(f"Saving to {OUT_PATH}...")
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
with open(OUT_PATH, "wb") as f:
    pickle.dump({"bm25": bm25, "index": page_index}, f)

size_mb = OUT_PATH.stat().st_size / (1024 * 1024)

print("\n" + "="*60)
print("STEP 4 COMPLETE")
print("="*60)
print(f"✓ BM25 index created: {OUT_PATH}")
print(f"✓ Size: {size_mb:.1f} MB")
print(f"✓ Indexed {len(page_index)} paragraphs from {len(set(r['order_number'] for r in page_index))} orders")

engine.dispose()
