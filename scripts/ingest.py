"""
RTI-Lens Ingestion Pipeline
- Primary source: TXT files in data/cic_orders_txt/
- Fallback: PDF files in data/cic_orders_pdf/ (only if no matching TXT)
- Extraction method flagged as 'txt', 'pdfplumber', or 'ocr'
"""

import os
import re
import json
import logging
from pathlib import Path
from datetime import datetime

import spacy
import pdfplumber
import pytesseract
from PIL import Image
from tqdm import tqdm
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# ── Config ────────────────────────────────────────────────────────────────────
DB_URL        = "postgresql://mohitsahoo@localhost:5432/rtilens"
TXT_DIR       = Path("data/cic_orders_txt")
PDF_DIR       = Path("data/cic_orders_pdf")
ALIASES_FILE  = Path("ministry_aliases.json")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ── Load resources ────────────────────────────────────────────────────────────
nlp = spacy.load("en_core_web_sm")

with open(ALIASES_FILE) as f:
    ministry_aliases = json.load(f)

# Build reverse map: alias (lowercased) → canonical name
alias_map = {}
for canonical, aliases in ministry_aliases.items():
    alias_map[canonical.lower()] = canonical
    for alias in aliases:
        alias_map[alias.lower()] = canonical

# ── Database setup ────────────────────────────────────────────────────────────
engine  = create_engine(DB_URL)
Session = sessionmaker(bind=engine)

# ── Regex patterns ────────────────────────────────────────────────────────────
RE_SECTION      = re.compile(r'Section\s+8\s*\(\s*1\s*\)\s*\(\s*([a-j])\s*\)', re.IGNORECASE)
RE_ORDER_NUM    = re.compile(r'CIC[/\-]\w+[/\-][A-Z][/\-]\d{4}[/\-]\d+', re.IGNORECASE)
RE_DATE_DMY     = re.compile(r'\b(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})\b')
RE_DATE_WRITTEN = re.compile(
    r'\b(\d{1,2})\s+(January|February|March|April|May|June|July|August|'
    r'September|October|November|December)\s*[,]?\s*(\d{4})\b', re.IGNORECASE
)
MONTH_MAP = {m: i+1 for i, m in enumerate([
    'january','february','march','april','may','june',
    'july','august','september','october','november','december'
])}


# ── Extraction helpers ─────────────────────────────────────────────────────────

def read_txt(path: Path) -> str:
    """Read a TXT file. Returns text or empty string."""
    try:
        return path.read_text(encoding='utf-8', errors='replace').strip()
    except Exception as e:
        log.warning(f"TXT read failed {path}: {e}")
        return ""

def extract_pdf_pdfplumber(path: Path) -> str:
    """Extract text from PDF using pdfplumber."""
    try:
        with pdfplumber.open(path) as pdf:
            return "\n\n".join(
                page.extract_text() or "" for page in pdf.pages
            ).strip()
    except Exception as e:
        log.warning(f"pdfplumber failed {path}: {e}")
        return ""

def extract_pdf_ocr(path: Path) -> str:
    """Fallback: OCR using pytesseract."""
    try:
        with pdfplumber.open(path) as pdf:
            pages_text = []
            for page in pdf.pages:
                img = page.to_image(resolution=200).original
                pages_text.append(pytesseract.image_to_string(img))
        return "\n\n".join(pages_text).strip()
    except Exception as e:
        log.warning(f"OCR failed {path}: {e}")
        return ""

def get_text_for_order(stem: str):
    """
    Returns (text, extraction_method).
    Priority: TXT file → pdfplumber → OCR.
    """
    txt_path = TXT_DIR / f"{stem}.txt"
    pdf_path = PDF_DIR / f"{stem}.pdf"

    # 1. TXT file exists — use it directly
    if txt_path.exists():
        text = read_txt(txt_path)
        if len(text) >= 100:
            return text, "txt"

    # 2. Fallback to PDF
    if pdf_path.exists():
        text = extract_pdf_pdfplumber(pdf_path)
        if len(text) >= 100:
            return text, "pdfplumber"
        # 3. Final fallback: OCR
        text = extract_pdf_ocr(pdf_path)
        if text:
            return text, "ocr"

    return "", "txt"  # empty — will be skipped


# ── Field extraction ──────────────────────────────────────────────────────────

def extract_order_number(text: str) -> str | None:
    m = RE_ORDER_NUM.search(text)
    return m.group(0).upper().replace('-', '/') if m else None

def extract_section(text: str) -> str | None:
    m = RE_SECTION.search(text)
    return f"8(1)({m.group(1).lower()})" if m else None

def extract_appeal_outcome(text: str) -> str | None:
    lower = text.lower()
    if re.search(r'(?<!not\s)partially allowed', lower):
        return 'partially_allowed'
    if re.search(r'(?<!not\s)\ballowed\b', lower):
        return 'allowed'
    if re.search(r'\b(dismissed|denied)\b', lower):
        return 'denied'
    return None

def extract_order_date(text: str):
    # Try DD/MM/YYYY
    m = RE_DATE_DMY.search(text)
    if m:
        try:
            return datetime(int(m.group(3)), int(m.group(2)), int(m.group(1))).date()
        except ValueError:
            pass
    # Try written date
    m = RE_DATE_WRITTEN.search(text)
    if m:
        try:
            month = MONTH_MAP[m.group(2).lower()]
            return datetime(int(m.group(3)), month, int(m.group(1))).date()
        except (ValueError, KeyError):
            pass
    return None

def extract_appeal_level(text: str) -> str | None:
    lower = text.lower()
    if 'second appeal' in lower:
        return 'second_appeal'
    if 'first appeal' in lower:
        return 'first_appeal'
    return None

def resolve_ministry(raw_text_content: str, session) -> int | None:
    """Match text against alias map. Insert new ministry if not found."""
    lower = raw_text_content.lower()
    for alias, canonical in alias_map.items():
        if alias in lower:
            # Get or create ministry row
            row = session.execute(
                text("SELECT id FROM ministries WHERE name = :name"),
                {"name": canonical}
            ).fetchone()
            if row:
                return row[0]
            result = session.execute(
                text("INSERT INTO ministries (name) VALUES (:name) RETURNING id"),
                {"name": canonical}
            )
            session.commit()
            return result.fetchone()[0]
    return None

def split_paragraphs(raw_text: str) -> list[str]:
    """Split text into paragraphs on double newlines. Min 50 chars per paragraph."""
    parts = re.split(r'\n\s*\n', raw_text)
    paragraphs = []
    for p in parts:
        p = p.strip()
        if len(p) >= 50:
            paragraphs.append(p)
    return paragraphs


# ── Main ingestion loop ───────────────────────────────────────────────────────

def ingest():
    session = Session()

    # Collect all stems (filenames without extension) from TXT dir
    txt_stems  = {p.stem for p in TXT_DIR.glob("*.txt")}
    pdf_stems  = {p.stem for p in PDF_DIR.glob("*.pdf")}
    all_stems  = txt_stems | pdf_stems

    log.info(f"Found {len(txt_stems)} TXT files, {len(pdf_stems)} PDF files, "
             f"{len(all_stems)} unique orders total.")

    inserted  = 0
    skipped   = 0
    failed    = 0

    for stem in tqdm(sorted(all_stems), desc="Ingesting orders"):
        raw_text, method = get_text_for_order(stem)

        if not raw_text:
            log.warning(f"No text extracted for: {stem}")
            failed += 1
            continue

        order_number = extract_order_number(raw_text) or stem
        section      = extract_section(raw_text)
        outcome      = extract_appeal_outcome(raw_text)
        order_date   = extract_order_date(raw_text)
        appeal_level = extract_appeal_level(raw_text)
        ministry_id  = resolve_ministry(raw_text, session)

        # Skip duplicate order numbers
        existing = session.execute(
            text("SELECT id FROM cases WHERE order_number = :order_number"),
            {"order_number": order_number}
        ).fetchone()
        if existing:
            skipped += 1
            continue

        # Insert case
        result = session.execute(text("""
            INSERT INTO cases
              (order_number, ministry_id, section_cited, appeal_outcome,
               appeal_level, order_date, extraction_method, raw_text)
            VALUES
              (:order_number, :ministry_id, :section_cited, :appeal_outcome,
               :appeal_level, :order_date, :extraction_method, :raw_text)
            RETURNING id
        """), {
            "order_number":      order_number,
            "ministry_id":       ministry_id,
            "section_cited":     section,
            "appeal_outcome":    outcome,
            "appeal_level":      appeal_level,
            "order_date":        order_date,
            "extraction_method": method,
            "raw_text":          raw_text,
        })
        case_id = result.fetchone()[0]

        # Insert paragraphs
        paragraphs = split_paragraphs(raw_text)
        for i, para_text in enumerate(paragraphs):
            session.execute(text("""
                INSERT INTO paragraphs (case_id, paragraph_index, text)
                VALUES (:case_id, :para_index, :text)
            """), {"case_id": case_id, "para_index": i, "text": para_text})

        session.commit()
        inserted += 1

    session.close()
    log.info(f"Done. Inserted: {inserted}, Skipped (duplicate): {skipped}, Failed: {failed}")


if __name__ == "__main__":
    ingest()
