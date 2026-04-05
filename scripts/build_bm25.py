"""
Builds bm25_pageindex.pkl from the paragraphs table.
Output: data/bm25_pageindex.pkl
  { "bm25": BM25Okapi, "index": list[dict] }
"""

import pickle
import logging
from pathlib import Path

import nltk
from nltk.corpus import stopwords
from rank_bm25 import BM25Okapi
from sqlalchemy import create_engine, text

DB_URL   = "postgresql://mohitsahoo@localhost:5432/rtilens"
OUT_PATH = Path("data/bm25_pageindex.pkl")

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

STOPWORDS = set(stopwords.words('english'))

def tokenize(text: str) -> list[str]:
    tokens = text.lower().split()
    return [t for t in tokens if t.isalpha() and t not in STOPWORDS]

engine = create_engine(DB_URL)

log.info("Loading paragraphs from DB...")
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

log.info(f"Loaded {len(rows)} paragraphs. Tokenizing...")

corpus_tokens = []
page_index    = []

for row in rows:
    tokens = tokenize(row.text)
    corpus_tokens.append(tokens)
    page_index.append({
        "paragraph_id":    row.id,
        "case_id":         row.case_id,
        "order_number":    row.order_number,
        "ministry":        row.ministry or "Unknown",
        "order_date":      str(row.order_date) if row.order_date else None,
        "paragraph_index": row.paragraph_index,
        "text":            row.text,
    })

log.info("Building BM25 index...")
bm25 = BM25Okapi(corpus_tokens)

log.info(f"Saving to {OUT_PATH}...")
with open(OUT_PATH, "wb") as f:
    pickle.dump({"bm25": bm25, "index": page_index}, f)

log.info(f"Done. Index covers {len(page_index)} paragraphs from "
         f"{len(set(r['order_number'] for r in page_index))} orders.")
