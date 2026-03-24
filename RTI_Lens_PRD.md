# RTI-Lens — Product Requirements Document
**Version:** 2.0 | **Status:** Final | **Date:** March 2026

> This PRD is written to be consumed directly by an LLM for code generation. Every section is precise, exhaustive, and implementation-ready.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Core Features](#2-core-features)
3. [Functional Requirements](#3-functional-requirements)
4. [Technical Architecture](#4-technical-architecture)
5. [Data Models](#5-data-models)
6. [API Design](#6-api-design)
7. [UI/UX Guidelines](#7-uiux-guidelines)
8. [Non-Functional Requirements](#8-non-functional-requirements)
9. [Edge Cases & Failure Handling](#9-edge-cases--failure-handling)
10. [Implementation Plan](#10-implementation-plan)

---

## 1. Project Overview

### 1.1 Problem Statement

India's RTI Act (2005) generates ~6 million applications per year. Citizens have no visibility into:
- Which government ministries systematically deny RTI requests and under which exemption clauses.
- How to phrase their RTI query to avoid rejection.
- Whether their appeal is likely to succeed.
- Whether their filing has been tampered with or lost.

The Central Information Commission (CIC) has issued 80,000+ publicly available ruling orders. This data is unstructured, unsearchable, and completely inaccessible to ordinary citizens. RTI-Lens mines this corpus to solve the four problems above.

### 1.2 Goals and Objectives

| # | Goal | Measurable Outcome |
|---|---|---|
| G1 | Expose denial patterns per ministry and per Section 8 clause | Ministry Denial Score computed for every ministry with ≥5 orders |
| G2 | Let citizens get grounded, cited answers from CIC precedents | Q&A retrieval precision@5 ≥ 70% on 20-query test set |
| G3 | Help citizens draft RTI queries that are less likely to be denied | 8/10 test queries rated as improved after reformulation |
| G4 | Predict appeal success probability | ML classifier F1 ≥ 0.65 on 20% held-out test set |
| G5 | Provide tamper-proof proof of RTI filing via blockchain | RTIRecord contract live and verifiable on Polygon Mumbai testnet |

### 1.3 Target Users

| Persona | Description | Primary Features Used |
|---|---|---|
| First-time RTI filer | Citizen, unfamiliar with legal phrasing, needs guidance | Co-Drafter, Denial Dashboard |
| RTI activist / journalist | Files multiple RTIs, needs pattern data and tamper-proof records | Denial Dashboard, Blockchain Filing |
| Legal researcher | Studies governance and transparency policy | RAG Q&A, Dataset export |
| Student evaluator | Assesses technical depth of the project | All features + ML metrics |

---

## 2. Core Features

### Feature 1 — Denial Analytics Dashboard

**Purpose:** Show which ministries and PIOs are serial deniers, which Section 8 exemption clauses are most abused, and what fraction of denials get overturned at CIC.

**User Flow:**
1. User lands on the Dashboard page.
2. User sees three pre-computed metrics rendered as interactive charts:
   - Bar chart: Top-10 ministries by denial rate (sorted descending).
   - Heatmap: Section 8 clause × Ministry — cell value = misuse rate (% denials overturned).
   - Line chart: CIC override rate by year (trend over time).
3. User can filter by ministry (dropdown), year range (slider), and Section 8 clause (multi-select).
4. All three charts update simultaneously when a filter is applied.
5. User can hover over any chart element to see exact counts and percentages in a tooltip.
6. User can click a ministry bar to drill down into a table of all CIC orders for that ministry.

**Edge Cases:**
- If a ministry has fewer than 5 orders in the dataset, exclude it from the bar chart and display a note: "Ministries with fewer than 5 orders are excluded for statistical reliability."
- If a filter combination returns 0 results, display: "No orders match this filter combination."
- If the dataset has not been loaded, display a loading skeleton, not a blank page.

---

### Feature 2 — RAG Q&A Interface (Vectorless, BM25-powered via PageIndex)

**Purpose:** Let citizens ask plain-English questions and receive grounded answers with exact citations from CIC orders.

**Retrieval Method:** BM25 via `rank_bm25` Python library (no vector embeddings, no dense retrieval). The BM25 index is built using a PageIndex structure — each indexed document unit = one paragraph from a CIC order, tagged with `order_id`, `date`, `ministry`, `paragraph_index`. The PageIndex maps BM25 document positions back to their source paragraph metadata, enabling source attribution without a vector store.

**User Flow:**
1. User navigates to the Q&A page.
2. User types a question in plain English.
3. System runs BM25 retrieval against the PageIndex → returns top-5 paragraphs with full metadata.
4. System sends a prompt to Claude Haiku API:
   - System prompt: "You are a legal assistant. Answer ONLY using the provided CIC order excerpts. Cite every claim with a paragraph reference [P1], [P2], etc. If the answer cannot be found in the provided excerpts, respond: 'No relevant precedent found in the retrieved orders.'"
   - User content: `<question>{user_query}</question><excerpts>{top_5_paragraphs_with_ids}</excerpts>`
5. LLM response is streamed to the UI.
6. A secondary faithfulness check call is made:
   - Prompt: "Given the answer and the source excerpts, identify any claim in the answer that cannot be traced to the excerpts. Return JSON: `{faithful: true/false, unsupported_claims: [...]}`"
   - If `faithful == false`, display a yellow warning banner: "⚠ Some claims could not be verified against source documents."
7. Sources panel renders below the answer — collapsible per citation — showing CIC order number, date, ministry, and full paragraph text.
8. Hard cap: max 3 LLM API calls per browser session.

**Edge Cases:**
- If BM25 returns 0 results, skip the LLM call and display: "No relevant CIC orders found for this query."
- If LLM API call fails, display: "AI response unavailable. Retrieved source paragraphs are shown below." — and still render the Sources panel.
- If faithfulness check API call fails, skip silently.

---

### Feature 3 — RTI Co-Drafting Assistant

**Purpose:** Accept a poorly-written RTI draft and return an improved version with inline explanations, backed by CIC precedents.

**User Flow:**
1. User selects Target Ministry (dropdown) and enters Draft RTI Query (textarea, min 20 chars, max 2000 chars).
2. On submit:
   - BM25 retrieves top-5 CIC rulings most relevant to the query text via PageIndex.
   - System queries denial analytics DB for the selected ministry to retrieve the top-3 most-denied Section 8 phrases.
   - System sends a single LLM prompt instructing the model to return JSON only:
     `{improved_query, change_notes: [{original, revised, reason}], avoid_phrases: [], sources_used: [order_id]}`
3. UI renders:
   - Before / After side-by-side view of original vs. improved query.
   - Change Notes: each change as a card with original → revised → reason.
   - Phrases to Avoid: pill list of risky phrases for the selected ministry.
   - Sources Panel: same collapsible format as Feature 2.

**Edge Cases:**
- Draft < 20 characters → inline validation error, no API call.
- Selected ministry has zero orders → run BM25 on all ministries + display notice.
- JSON parsing of LLM response fails → display raw text, log parsing error.

---

### Feature 4 — Appeal Outcome Predictor

**Purpose:** Predict the probability that a CIC appeal will succeed.

**User Flow:**
1. User fills in: Ministry, Section 8 clause cited, Appeal level (First / Second), Year of filing.
2. Frontend POSTs to `/api/predict`.
3. Backend runs scikit-learn model inference and returns probability + explanation.
4. UI renders a circular progress indicator (probability %), plain-language explanation, and a collapsible model card.

**Edge Cases:**
- Ministry + section combination has < 10 training samples → return `low_data_warning: true`.
- Model file missing at startup → return HTTP 503, show "Unavailable" state in UI.

---

### Feature 5 — Blockchain RTI Filing (Trust Anchor)

**Purpose:** Generate an immutable SHA-256 hash of an RTI filing stored on the Polygon blockchain, with 30-day deadline tracking.

**User Flow:**
1. User fills in: Applicant Name, Target Authority, RTI Query.
2. On "Preview Hash": frontend computes SHA-256 client-side via Web Crypto API and displays it.
3. On "Confirm & File": frontend POSTs to `/api/blockchain/file`. Backend calls Solidity contract via web3.py. Returns TX hash and Polygonscan URL.
4. UI renders confirmation card with TX hash, Polygonscan link, and 30-day countdown.
5. User can later enter TX hash to check deadline status and appeal status.

**Edge Cases:**
- Transaction confirmation > 30 seconds → return TX hash with "pending" status.
- Contract call reverts → return revert reason to UI.

---

## 3. Functional Requirements

### 3.1 Data Ingestion Pipeline (Offline Script)

**Input:** Folder of CIC order PDFs at `/data/cic_orders/`  
**Output:** Populated PostgreSQL database + serialized BM25 PageIndex

**Steps:**

1. Iterate over every `.pdf` in `/data/cic_orders/`.
2. Attempt text extraction with `pdfplumber`. If extracted text length < 100 characters, fall back to `pytesseract` OCR. Flag OCR records with `extraction_method = 'ocr'`.
3. Run spaCy + regex to extract:
   - `ministry`: match extracted text against `ministry_aliases.json` (dict of canonical name → list of aliases).
   - `section_cited`: regex `Section\s+8\s*\(\s*1\s*\)\s*\([a-j]\)` → normalize to `8(1)(x)` format.
   - `appeal_outcome`: keyword match — "allowed" (not preceded by "not") → `allowed`; "dismissed" or "denied" → `denied`; "partially allowed" → `partially_allowed`.
   - `order_date`: regex for DD/MM/YYYY or Month DD, YYYY formats.
   - `order_number`: regex for CIC order number patterns (e.g., `CIC/SA/A/YYYY/NNNNNN`).
4. Insert each record into the `cases` table. On duplicate `order_number`, skip.
5. Split order text into paragraphs on `\n\n` or sentence groups of ≥ 3 sentences. Insert each paragraph into the `paragraphs` table.
6. **Build PageIndex:**
   - Collect all paragraphs from the `paragraphs` table.
   - Build a Python list `corpus_tokens`: each element = tokenized paragraph (lowercase, stopwords removed, no stemming).
   - Build a parallel list `page_index`: each element = `{paragraph_id, case_id, order_number, ministry, order_date, paragraph_index}`.
   - Instantiate `BM25Okapi(corpus_tokens)`.
   - Serialize both `bm25_model` and `page_index` together to `/data/bm25_pageindex.pkl` as `{bm25: BM25Okapi, index: list[dict]}`.
7. Export `cases` table to `/data/cases.csv`.
8. Run `scripts/compute_stats.py` to populate `ministry_stats` and `section_stats`.
9. Run `scripts/train_classifier.py` to produce `model.pkl` and `model_card.json`.

---

### 3.2 BM25 PageIndex Retrieval (Runtime)

**Startup:** Load `/data/bm25_pageindex.pkl` once at FastAPI startup. Store in a module-level singleton `PAGEINDEX = {bm25, index}`.

**Function:** `retrieve(query: str, k: int = 5) -> list[dict]`

```python
def retrieve(query: str, k: int = 5) -> list[dict]:
    tokens = tokenize(query)          # lowercase, remove stopwords
    if not tokens:
        return []
    scores = PAGEINDEX["bm25"].get_scores(tokens)
    top_k_positions = scores.argsort()[-k:][::-1]
    top_k_positions = [i for i in top_k_positions if scores[i] > 0]
    return [PAGEINDEX["index"][i] | {"score": float(scores[i])} for i in top_k_positions]
```

Each returned dict contains: `paragraph_id`, `case_id`, `order_number`, `ministry`, `order_date`, `paragraph_index`, `text`, `score`.

---

### 3.3 ML Classifier Training (Offline Script)

**Script:** `scripts/train_classifier.py`  
**Input:** `/data/cases.csv`

**Feature engineering:**
- `ministry` → `LabelEncoder` (fit on training set only)
- `section_cited` → `LabelEncoder`
- `appeal_level` → binary: 0 = first_appeal, 1 = second_appeal
- `year` → integer extracted from `order_date`
- `order_text` → `TfidfVectorizer(max_features=500, ngram_range=(1,2))` fit on training set only

**Target:** `appeal_outcome` → binary: 1 = allowed, 0 = denied or partially_allowed

**Training steps:**
1. Load CSV. Drop rows where `appeal_outcome` is null.
2. 80/20 stratified train/test split (`random_state=42`).
3. Build `Pipeline(ColumnTransformer → LogisticRegression(max_iter=1000))`.
4. Also train `RandomForestClassifier(n_estimators=100)`.
5. Evaluate both on test set. Log accuracy, precision, recall, F1, confusion matrix.
6. Serialize the better-performing model to `/data/model.pkl`.
7. Serialize `model_card.json`: `{model_type, accuracy, f1, training_size, test_size, feature_names, class_distribution, low_data_threshold: 10}`.

---

### 3.4 Blockchain Contract Interaction (Runtime)

**Startup:** Load `CONTRACT_ADDRESS` and `PRIVATE_KEY` from env. Initialize `Web3(Web3.HTTPProvider(POLYGON_MUMBAI_RPC_URL))`.

**fileRTI(hash_hex, timestamp_unix):**
1. `hash_bytes32 = Web3.to_bytes(hexstr=hash_hex)`
2. Build transaction via `contract.functions.fileRTI(hash_bytes32, timestamp_unix).build_transaction(...)`.
3. Sign with platform private key. Send raw transaction.
4. Poll for receipt every 2 seconds, max 30 seconds.
5. Return `{tx_hash, block_number, status}`.

**getRecord(filing_id):**
1. Call (read-only): `contract.functions.getRecord(filing_id).call()`.
2. Return struct fields as a dict.

---

## 4. Technical Architecture

### 4.1 Tech Stack

| Layer | Technology | Version |
|---|---|---|
| Frontend | React | 18.x |
| Frontend build | Vite | 5.x |
| Frontend styling | Tailwind CSS | 3.x |
| Frontend state | Zustand | 4.x |
| Frontend charts | Recharts | 2.x |
| Frontend routing | React Router | 6.x |
| Frontend HTTP | Axios | 1.x |
| Backend | FastAPI | 0.111.x |
| Backend runtime | Python | 3.11 |
| Database | PostgreSQL | 16.x |
| ORM | SQLAlchemy | 2.x |
| PDF extraction | pdfplumber | 0.10.x |
| OCR fallback | pytesseract | 0.3.x |
| NLP | spaCy | 3.7.x (en_core_web_sm) |
| BM25 | rank_bm25 | 0.2.x |
| ML | scikit-learn | 1.4.x |
| LLM | Claude Haiku API | claude-haiku-4-5 |
| Blockchain | Polygon Mumbai testnet | — |
| Blockchain lib | web3.py | 6.x |
| Smart contract | Solidity | 0.8.x |
| Contract tooling | Hardhat | 2.x |
| Containerization | Docker + docker-compose | — |
| Deployment | Vercel (frontend) + Railway (backend) | — |

### 4.2 High-Level System Design

```
┌──────────────────────────────────────────────────────────┐
│                     React Frontend                        │
│  Dashboard | Q&A | Co-Drafter | File & Verify            │
└────────────────────┬─────────────────────────────────────┘
                     │ HTTP REST (JSON)
┌────────────────────▼─────────────────────────────────────┐
│                   FastAPI Backend                         │
│                                                          │
│  /api/analytics  /api/qa  /api/draft  /api/predict       │
│  /api/blockchain                                         │
│                                                          │
│  ┌──────────────────┐  ┌──────────┐  ┌───────────────┐  │
│  │ BM25 + PageIndex │  │ sklearn  │  │ Anthropic API │  │
│  │  (in memory)     │  │  model   │  │ (Claude Haiku)│  │
│  └──────────────────┘  └──────────┘  └───────────────┘  │
│                                                          │
│  ┌─────────────┐  ┌──────────────────────────────────┐  │
│  │ PostgreSQL  │  │ Web3.py → Polygon Mumbai Testnet  │  │
│  └─────────────┘  └──────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

### 4.3 Data Flow — Q&A Request

```
User types query
      ↓
React: POST /api/qa { query, session_id }
      ↓
FastAPI: tokenize → BM25 PageIndex → top-5 paragraphs + metadata
      ↓
FastAPI: build prompt + call Claude Haiku (call #1)
      ↓
FastAPI: run faithfulness check (call #2)
      ↓
FastAPI: return { answer, sources, faithful, calls_remaining }
      ↓
React: render answer + Sources Panel + faithfulness banner
```

### 4.4 Data Flow — RTI Co-Drafting

```
User inputs: ministry + draft query
      ↓
React: POST /api/draft { ministry_id, draft_query, session_id }
      ↓
FastAPI: BM25 PageIndex retrieval on draft text → top-5 paragraphs
FastAPI: query section_stats for ministry → top-3 denied phrases
      ↓
FastAPI: build reformulation prompt + call Claude Haiku
      ↓
FastAPI: parse JSON response → return { improved_query, change_notes, avoid_phrases, sources }
      ↓
React: render Before/After, Change Notes, Avoid Phrases, Sources Panel
```

### 4.5 Data Flow — Blockchain Filing

```
User fills form (name, authority, query)
      ↓
React: Web Crypto API → SHA-256(name + authority + query + timestamp)
React: display hash preview
      ↓
User confirms → React: POST /api/blockchain/file { hash, timestamp, name, authority }
      ↓
FastAPI: web3.py → contract.fileRTI(hash_bytes32, timestamp)
FastAPI: poll receipt (max 30s)
FastAPI: insert into blockchain_filings table
      ↓
FastAPI: return { tx_hash, polygonscan_url, block_number, deadline }
      ↓
React: render confirmation card + countdown
```

---

## 5. Data Models

### 5.1 PostgreSQL Schema

```sql
-- Ministry master list
CREATE TABLE ministries (
    id       SERIAL PRIMARY KEY,
    name     TEXT NOT NULL UNIQUE,
    aliases  TEXT[]
);

-- CIC orders (one row per order)
CREATE TABLE cases (
    id                SERIAL PRIMARY KEY,
    order_number      TEXT UNIQUE NOT NULL,
    order_url         TEXT,
    ministry_id       INTEGER REFERENCES ministries(id),
    section_cited     TEXT,
    appeal_outcome    TEXT CHECK (appeal_outcome IN ('allowed', 'denied', 'partially_allowed')),
    appeal_level      TEXT CHECK (appeal_level IN ('first_appeal', 'second_appeal')),
    order_date        DATE,
    extraction_method TEXT CHECK (extraction_method IN ('pdfplumber', 'ocr')),
    raw_text          TEXT,
    created_at        TIMESTAMPTZ DEFAULT NOW()
);

-- Paragraph-level index (for PageIndex source attribution)
CREATE TABLE paragraphs (
    id              SERIAL PRIMARY KEY,
    case_id         INTEGER REFERENCES cases(id) ON DELETE CASCADE,
    paragraph_index INTEGER NOT NULL,
    text            TEXT NOT NULL
);

-- Pre-computed analytics (refreshed after each ingestion run)
CREATE TABLE ministry_stats (
    ministry_id     INTEGER PRIMARY KEY REFERENCES ministries(id),
    total_orders    INTEGER,
    denied_count    INTEGER,
    allowed_count   INTEGER,
    partially_count INTEGER,
    denial_rate     FLOAT,
    override_rate   FLOAT,
    last_computed   TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE section_stats (
    section_cited     TEXT,
    ministry_id       INTEGER REFERENCES ministries(id),
    total_citations   INTEGER,
    overturned_count  INTEGER,
    misuse_rate       FLOAT,
    PRIMARY KEY (section_cited, ministry_id)
);

-- Blockchain filings
CREATE TABLE blockchain_filings (
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
```

### 5.2 Example Rows

**cases:**
```json
{
  "id": 1,
  "order_number": "CIC/SA/A/2023/001234",
  "ministry_id": 3,
  "section_cited": "8(1)(j)",
  "appeal_outcome": "allowed",
  "appeal_level": "second_appeal",
  "order_date": "2023-06-14",
  "extraction_method": "pdfplumber"
}
```

**paragraphs:**
```json
{
  "id": 12,
  "case_id": 1,
  "paragraph_index": 2,
  "text": "The Commission finds that the PIO's invocation of Section 8(1)(j) is not justified as the information sought does not relate to personal information that would cause unwarranted invasion of privacy."
}
```

**PageIndex entry (in-memory, not a DB table):**
```json
{
  "paragraph_id": 12,
  "case_id": 1,
  "order_number": "CIC/SA/A/2023/001234",
  "ministry": "Ministry of Finance",
  "order_date": "2023-06-14",
  "paragraph_index": 2,
  "text": "The Commission finds that...",
  "score": 4.82
}
```

---

## 6. API Design

**Base URL:** `https://api.rtilens.app` (local: `http://localhost:8000`)  
**Auth:** No authentication for MVP. Rate limiting: 60 req/min per IP via `slowapi`.  
**Content-Type:** `application/json` on all endpoints.

---

### GET /api/analytics/denial-rates

**Query params:** `ministry_id` (int?), `section` (str?), `year_from` (int?), `year_to` (int?), `limit` (int, default 10)

**Response 200:**
```json
{
  "ministries": [
    {
      "ministry_id": 3,
      "ministry_name": "Ministry of Finance",
      "total_orders": 342,
      "denial_rate": 0.68,
      "override_rate": 0.41,
      "top_section": "8(1)(j)"
    }
  ],
  "total_ministries": 45,
  "dataset_size": 500
}
```

---

### GET /api/analytics/section-heatmap

**Response 200:**
```json
{
  "data": [
    { "section": "8(1)(j)", "ministry": "Finance", "misuse_rate": 0.62 },
    { "section": "8(1)(d)", "ministry": "Home Affairs", "misuse_rate": 0.44 }
  ]
}
```

---

### GET /api/analytics/override-trend

**Response 200:**
```json
{
  "trend": [
    { "year": 2018, "override_rate": 0.38 },
    { "year": 2019, "override_rate": 0.41 }
  ]
}
```

---

### GET /api/analytics/ministry/{ministry_id}/orders

**Response 200:**
```json
{
  "orders": [
    {
      "order_number": "CIC/SA/A/2023/001234",
      "section_cited": "8(1)(j)",
      "appeal_outcome": "allowed",
      "order_date": "2023-06-14",
      "order_url": "https://cic.gov.in/..."
    }
  ],
  "total": 342
}
```

---

### POST /api/qa

**Request:**
```json
{ "query": "What happens if a PIO cites Section 8(1)(j) incorrectly?", "session_id": "uuid-string" }
```

**Response 200:**
```json
{
  "answer": "When a PIO incorrectly invokes Section 8(1)(j) [P1], the CIC has consistently held...",
  "citations": ["P1", "P2"],
  "sources": [
    {
      "citation_id": "P1",
      "paragraph_id": 12,
      "order_number": "CIC/SA/A/2023/001234",
      "order_date": "2023-06-14",
      "ministry": "Ministry of Finance",
      "text": "The Commission finds that the PIO's invocation..."
    }
  ],
  "faithful": true,
  "unsupported_claims": [],
  "calls_remaining": 2
}
```

**Response 404:**
```json
{ "error": "NO_RESULTS", "message": "No relevant CIC orders found for this query." }
```

**Response 429:**
```json
{ "error": "SESSION_LIMIT_REACHED", "message": "Maximum 3 AI calls per session." }
```

**Response 502:**
```json
{ "error": "LLM_UNAVAILABLE", "message": "AI response unavailable.", "sources": [...] }
```

---

### POST /api/draft

**Request:**
```json
{
  "ministry_id": 3,
  "draft_query": "I want to know about files in the Finance ministry",
  "session_id": "uuid-string"
}
```

**Response 200:**
```json
{
  "improved_query": "Please provide certified copies of all file notings...",
  "change_notes": [
    {
      "original": "I want to know about files",
      "revised": "Please provide certified copies of all file notings and decisions",
      "reason": "RTIs that specify the exact document type are 34% less likely to receive a Section 8(1)(d) denial."
    }
  ],
  "avoid_phrases": ["I want to know", "any information", "all documents"],
  "sources": [
    {
      "order_number": "CIC/SA/A/2022/005678",
      "ministry": "Ministry of Finance",
      "order_date": "2022-03-21",
      "text": "The Commission noted that vague requests..."
    }
  ]
}
```

**Response 422:**
```json
{ "error": "VALIDATION_ERROR", "field": "draft_query", "message": "Minimum 20 characters required." }
```

---

### POST /api/predict

**Request:**
```json
{
  "ministry_id": 3,
  "section_cited": "8(1)(j)",
  "appeal_level": "second_appeal",
  "year": 2023
}
```

**Response 200:**
```json
{
  "probability": 0.73,
  "label": "Likely to succeed",
  "confidence": "moderate",
  "explanation": "Appeals against Ministry of Finance citing Section 8(1)(j) at the CIC level succeed approximately 73% of the time in this dataset.",
  "low_data_warning": false,
  "model_card": {
    "model_type": "LogisticRegression",
    "accuracy": 0.68,
    "f1": 0.66,
    "training_size": 400,
    "test_size": 100,
    "disclaimer": "This prediction is based on historical data and is not legal advice."
  }
}
```

**Response 503:**
```json
{ "error": "MODEL_UNAVAILABLE", "message": "Predictor temporarily unavailable." }
```

---

### POST /api/blockchain/file

**Request:**
```json
{
  "hash": "a3f1b2c4d5e6...",
  "timestamp": "2026-03-24T10:30:00Z",
  "applicant_name": "Ravi Kumar",
  "authority": "Ministry of Finance",
  "query_text": "Please provide..."
}
```

**Response 200:**
```json
{
  "tx_hash": "0xabc123...",
  "block_number": 45123456,
  "contract_address": "0xdef456...",
  "polygonscan_url": "https://mumbai.polygonscan.com/tx/0xabc123...",
  "deadline": "2026-04-23T10:30:00Z"
}
```

**Response 408:**
```json
{ "error": "TX_TIMEOUT", "tx_hash": "0xabc123...", "message": "Transaction submitted but not confirmed." }
```

**Response 400:**
```json
{ "error": "CONTRACT_REVERT", "reason": "Hash already filed." }
```

---

### GET /api/blockchain/status/{tx_hash}

**Response 200:**
```json
{
  "filing_hash": "a3f1b2c4...",
  "filing_timestamp": "2026-03-24T10:30:00Z",
  "deadline": "2026-04-23T10:30:00Z",
  "deadline_breached": false,
  "appeal_status": 0,
  "appeal_status_label": "Pending",
  "days_remaining": 29
}
```

**Response 404:**
```json
{ "error": "NOT_FOUND", "message": "No filing found for this transaction hash." }
```

---

## 7. UI/UX Guidelines

### 7.1 Application Structure

```
/           → Dashboard (Denial Analytics)
/qa         → RAG Q&A Interface
/draft      → Co-Drafter + Appeal Predictor
/file       → File & Verify (Blockchain)
```

**Global layout:** Fixed left sidebar (240px) with nav links and RTI-Lens logo. Main content area fills remaining viewport width. No top navbar. Sidebar collapses to 64px icon-only on screens < 1024px.

---

### 7.2 Page: Dashboard (`/`)

**Components and behavior:**

`<FilterBar />` — sticky at top of content area. Contains:
- Ministry dropdown (searchable via react-select, populated from `/api/analytics/denial-rates`).
- Year range slider (2006–2026, dual handle).
- Section multi-select (8(1)(a)–8(1)(j) as checkboxes).
- "Reset Filters" button.
- Filter changes trigger API calls debounced at 300ms.

`<DenialBarChart />` — Recharts `BarChart`. X-axis: ministry name (truncated to 20 chars, tooltip shows full name). Y-axis: denial rate (0–1, displayed as %). Bars sorted descending. Click on a bar → sets `selectedMinistry` in Zustand store, renders `<OrdersTable />`.

`<SectionHeatmap />` — Recharts custom cell grid. X-axis: section clauses. Y-axis: ministries. Cell color scale: `#f0f9ff` (low) → `#dc2626` (high). Tooltip: exact misuse rate and citation count.

`<OverrideTrendLine />` — Recharts `LineChart`. X: year. Y: override rate (%). Single line with dot markers.

`<OrdersTable />` — visible only when `selectedMinistry !== null`. Columns: Order Number (external link to `order_url`), Section Cited, Outcome (color-coded badge: green/red/yellow), Date. 20 rows per page, pagination controls.

---

### 7.3 Page: Q&A (`/qa`)

**Components and behavior:**

`<SessionCounter />` — top right: "AI calls remaining: X/3". Updated after each API response.

`<QueryInput />` — full-width textarea (3 rows). Submit button: "Search CIC Orders". Enter submits (Shift+Enter = newline). Disabled while loading.

`<LoadingSkeleton />` — shown during API call: three animated grey placeholder lines.

`<AnswerPanel />` — renders LLM answer text. Superscript citation numbers (`[P1]`, `[P2]`) are `<button>` elements that scroll to and expand the corresponding source card.

`<FaithfulnessBanner />` — renders only if `faithful === false`. Yellow background, warning icon, text: "⚠ Some claims could not be verified against source documents."

`<SourcesPanel />` — list of `<SourceCard />` components. Each card: header shows order number + date + ministry. Body shows paragraph text. Collapsed by default, expanded on click or when linked from a citation superscript.

---

### 7.4 Page: Co-Drafter (`/draft`)

**Layout:** Two-column. Left (60%): input + output. Right (40%): Appeal Predictor panel.

**Left column:**

`<MinistrySelect />` — required searchable dropdown.

`<DraftTextarea />` — min 20 chars. Character counter shown below (e.g., "47 / 2000"). Inline error shown if submitted below minimum.

`<SubmitButton />` — "Improve My RTI". Disabled until ministry selected and char minimum met.

`<BeforeAfter />` — two stacked text boxes after response: "Your Draft" (grey background, read-only) and "Improved Query" (white background, read-only, with "Copy" button).

`<ChangeNotes />` — accordion list. Each item: "Original" text in red with strikethrough → "Revised" text in green → "Reason" paragraph.

`<AvoidList />` — horizontal wrap of pill badges. Each pill: red border, small monospace text.

`<SourcesPanel />` — same component as Q&A page.

**Right column:**

`<PredictorForm />` — Ministry field auto-populated from left column selection (read-only). Section dropdown (8(1)(a)–8(1)(j)). Appeal level radio. Year number input (2006–2026).

`<ProbabilityMeter />` — SVG arc gauge (180° sweep). Color: green > 60%, yellow 40–60%, red < 40%. Center label: "73%". Below: label text ("Likely to succeed").

`<PredictorExplanation />` — plain-text explanation sentence from API.

`<ModelCard />` — collapsible section at bottom of right column. Shows: model type, accuracy, F1, training size, disclaimer text.

---

### 7.5 Page: File & Verify (`/file`)

**Components:**

`<FilingForm />` — three required text inputs: Applicant Name, Target Authority, RTI Query (textarea). "Preview Hash" button becomes active when all three fields are non-empty.

`<HashPreview />` — shown after "Preview Hash" click. Monospace hash string (truncated to 16 chars + "..." + last 8 chars, with full hash in tooltip). Timestamp used. Explanatory note: "This hash uniquely identifies your filing. No personal data is stored on the blockchain."

`<ConfirmButton />` — "Confirm & File on Blockchain". Shows spinner and "Submitting to Polygon..." during transaction.

`<ConfirmationCard />` — shown after success:
- TX hash (truncated, copy button).
- "View on Polygonscan" external link button.
- Filing timestamp.
- Deadline date.
- Days remaining countdown (integer days).

`<StatusLookup />` — second section on the page. Input: TX hash. Button: "Check Status". Returns a status card showing: deadline breach flag (red alert if breached), appeal status badge, days remaining.

---

## 8. Non-Functional Requirements

### 8.1 Performance

- Analytics endpoints (`/api/analytics/*`): response time < 200ms. Data is pre-computed in `ministry_stats` and `section_stats` tables; no aggregation at request time.
- BM25 PageIndex retrieval: < 100ms for a 500-order corpus. Index is in-memory singleton.
- LLM API call: frontend shows loading state immediately. Timeout after 30 seconds.
- Blockchain TX submission: < 5 seconds. Confirmation polling up to 30 seconds.
- React frontend initial load (Vite bundle, gzipped): < 2 seconds on a 4G connection.

### 8.2 Scalability

- The BM25 PageIndex and PostgreSQL schema scale to 80,000 CIC orders with no code changes. At 80K orders, the serialized `bm25_pageindex.pkl` is estimated at < 500MB in memory.
- The ML model is retrained by re-running `scripts/train_classifier.py` on an updated `cases.csv`.
- FastAPI is stateless. Multiple instances run behind a load balancer. The in-memory BM25 index is loaded per instance at startup.
- The session call counter (in-memory dict) must be replaced with Redis if multiple FastAPI instances are deployed.

### 8.3 Security

- `ANTHROPIC_API_KEY`, `PRIVATE_KEY`, `DATABASE_URL`, and `POLYGON_RPC_URL` are loaded from environment variables only. Never hardcoded or committed to source control.
- The blockchain platform wallet holds only test MATIC. No real funds at risk in MVP.
- Rate limiting: 60 requests/minute per IP via `slowapi` middleware.
- Session call counter stored server-side (in-memory dict, 1-hour TTL per `session_id`).
- All SQL queries use SQLAlchemy ORM with parameterized statements. No raw string interpolation.
- No PII stored on-chain. Only the SHA-256 hash is written to the Solidity contract. Applicant name and query text are stored in the `blockchain_filings` PostgreSQL table only.
- CORS: FastAPI configured to allow requests only from the deployed Vercel frontend origin.

---

## 9. Edge Cases & Failure Handling

| Scenario | System Response |
|---|---|
| PDF has no extractable text (scanned) | Fall back to pytesseract OCR. Flag record `extraction_method = 'ocr'`. Continue pipeline. |
| spaCy fails to extract `section_cited` | Store `section_cited = NULL`. Record still inserted. Excluded from section-level analytics. |
| spaCy fails to extract `appeal_outcome` | Store `appeal_outcome = NULL`. Excluded from ML training. |
| Ministry name not in `ministry_aliases.json` | Store raw extracted string. Create new ministry row. |
| BM25 returns 0 results for a query | Return HTTP 404 `NO_RESULTS`. Do not call LLM. Render friendly message on frontend. |
| Claude Haiku API call fails (any HTTP error) | Return HTTP 502 `LLM_UNAVAILABLE`. Frontend renders Sources Panel with raw retrieved paragraphs. |
| Faithfulness check API call fails | Log error. Return `faithful: true` as default. Do not block main answer. |
| LLM returns malformed JSON (Co-Drafter) | Catch `json.JSONDecodeError`. Return raw text in `improved_query`. Set `change_notes: []`. |
| Session limit reached (3 calls) | Return HTTP 429 `SESSION_LIMIT_REACHED`. Frontend disables Q&A and Draft submit buttons and shows explanation. |
| ML `model.pkl` missing at startup | Log CRITICAL. `/api/predict` returns HTTP 503. Predictor panel renders "Unavailable" state. |
| Blockchain TX times out (> 30s) | Return HTTP 408 `TX_TIMEOUT` with `tx_hash`. Frontend shows pending state with Polygonscan link if hash is available. |
| Blockchain contract call reverts | Catch `ContractLogicError`. Return HTTP 400 with revert reason string. |
| Ministry has < 10 training samples | Return prediction with `low_data_warning: true`. Frontend shows yellow badge next to probability. |
| Database connection lost | FastAPI health check fails. All endpoints return HTTP 503. Logged as CRITICAL. |
| Filter combination returns 0 results | Return `{ ministries: [], total_ministries: 0 }`. Frontend renders: "No orders match this filter combination." |
| Draft query < 20 characters | Return HTTP 422 `VALIDATION_ERROR` without calling LLM. Frontend shows inline validation. |
| User submits same hash twice to blockchain | Contract reverts with "Hash already filed." Return HTTP 400 `CONTRACT_REVERT`. |
| PageIndex pickle file missing at startup | Log CRITICAL. `/api/qa` and `/api/draft` return HTTP 503. Frontend shows "Search unavailable" state. |

---

## 10. Implementation Plan

### Phase 1 — Data Pipeline & Database (Week 1–2)

**Goal:** Working ingestion pipeline that produces a populated PostgreSQL database and CSV.

1. Set up PostgreSQL via Docker. Define schema from Section 5.1. Run migrations with Alembic.
2. Collect 500 CIC PDFs from cic.gov.in.
3. Build `scripts/ingest.py`: pdfplumber → OCR fallback → spaCy extraction → PostgreSQL insert.
4. Build `ministry_aliases.json` with ~50 ministry name variants.
5. Validate: manually verify 50 records. Target ≥ 85% field extraction accuracy.
6. Export `cases.csv`.

**Deliverable:** Populated `cases` and `paragraphs` tables with 500+ rows. Validated CSV.

---

### Phase 2 — Analytics Engine & ML Classifier (Week 2–3)

**Goal:** Pre-computed stats tables + trained model on disk.

1. Write `scripts/compute_stats.py`: populate `ministry_stats` and `section_stats`.
2. Write `scripts/train_classifier.py`: feature engineering, train LR + RF, serialize best model.
3. Build FastAPI analytics endpoints.
4. Write pytest unit tests for stats computation (10 test cases minimum).

**Deliverable:** All analytics API endpoints return correct data. `model.pkl` and `model_card.json` serialized.

---

### Phase 3 — BM25 PageIndex & Q&A API (Week 3–4)

**Goal:** Working RAG Q&A API with PageIndex source attribution and faithfulness check.

1. Write `scripts/build_index.py`: tokenize paragraphs, build `BM25Okapi`, build `page_index` list, serialize to `bm25_pageindex.pkl`.
2. Implement `retrieve()` function using the PageIndex.
3. Build `POST /api/qa`: retrieval → LLM prompt → faithfulness check → structured response.
4. Implement session call counter (in-memory dict, 1-hour TTL).
5. Write integration tests: 5 queries with expected top-1 retrieved order.

**Deliverable:** `/api/qa` returns grounded answers with full source attribution from PageIndex.

---

### Phase 4 — Co-Drafting & Predictor API (Week 4–5)

**Goal:** Working Co-Drafter and Predictor APIs.

1. Build `POST /api/draft`: BM25 PageIndex retrieval + section_stats denied phrases → LLM reformulation → parse JSON.
2. Build `POST /api/predict`: load `model.pkl`, run inference, return structured response.
3. Write unit tests: 5 draft inputs, 5 predict inputs.

**Deliverable:** Both endpoints return correctly structured responses.

---

### Phase 5 — Blockchain Contract & API (Week 5–6)

**Goal:** RTIRecord contract live on Polygon Mumbai testnet, integrated with FastAPI.

1. Write `contracts/RTIRegistry.sol` (see Appendix A).
2. Write Hardhat test suite: filing, response recording, deadline flag (5-second demo deadline in tests).
3. Deploy to Polygon Mumbai testnet via Hardhat deploy script. Record `CONTRACT_ADDRESS`.
4. Write `blockchain/client.py`: Web3.py wrapper for `fileRTI()` and `getRecord()`.
5. Build `POST /api/blockchain/file` and `GET /api/blockchain/status/{tx_hash}`.
6. Insert filing record into `blockchain_filings` table after confirmation.

**Deliverable:** RTI filing generates a real Polygonscan link. Deadline flag demo works in < 5 minutes.

---

### Phase 6 — React Frontend (Week 6–8)

**Goal:** Fully functional 4-page React app connected to all API endpoints.

1. Scaffold Vite + React 18 + Tailwind CSS + Zustand project. Configure React Router.
2. Build global `<Sidebar />` with navigation links.
3. Build Dashboard: `<FilterBar />`, `<DenialBarChart />`, `<SectionHeatmap />`, `<OverrideTrendLine />`, `<OrdersTable />`.
4. Build Q&A: `<QueryInput />`, `<AnswerPanel />`, `<SourcesPanel />`, `<FaithfulnessBanner />`, `<SessionCounter />`.
5. Build Co-Drafter: `<BeforeAfter />`, `<ChangeNotes />`, `<AvoidList />`, `<SourcesPanel />` + `<PredictorForm />`, `<ProbabilityMeter />`, `<ModelCard />`.
6. Build File & Verify: `<FilingForm />`, `<HashPreview />`, `<ConfirmationCard />`, `<StatusLookup />`.
7. Connect all components to API via Axios. Handle loading, error, and empty states for every endpoint.
8. Write Vitest component tests for `<SourcesPanel />`, `<ProbabilityMeter />`, `<HashPreview />`.
9. Deploy frontend to Vercel, backend to Railway.

**Deliverable:** Fully deployed, end-to-end functional RTI-Lens on Vercel + Railway + Polygon Mumbai.

---

## Appendix A — Solidity Smart Contract

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract RTIRegistry {
    struct RTIRecord {
        bytes32 filingHash;
        uint256 filingTimestamp;
        bytes32 responseHash;
        uint256 responseTimestamp;
        bool deadlineBreached;
        uint8 appealStatus; // 0=pending 1=first_appeal 2=CIC 3=resolved
    }

    mapping(uint256 => RTIRecord) public records;
    mapping(bytes32 => bool) public hashExists;
    uint256 public recordCount;
    uint256 public constant DEADLINE_PERIOD = 30 days;

    event RTIFiled(uint256 indexed id, bytes32 filingHash, uint256 timestamp);
    event DeadlineBreached(uint256 indexed id);
    event AppealStatusUpdated(uint256 indexed id, uint8 status);

    function fileRTI(bytes32 _hash, uint256 _timestamp) external returns (uint256) {
        require(!hashExists[_hash], "Hash already filed.");
        hashExists[_hash] = true;
        recordCount++;
        records[recordCount] = RTIRecord({
            filingHash: _hash,
            filingTimestamp: _timestamp,
            responseHash: bytes32(0),
            responseTimestamp: 0,
            deadlineBreached: false,
            appealStatus: 0
        });
        emit RTIFiled(recordCount, _hash, _timestamp);
        return recordCount;
    }

    function recordResponse(uint256 _id, bytes32 _responseHash) external {
        RTIRecord storage r = records[_id];
        require(r.filingTimestamp > 0, "Record not found.");
        require(r.responseHash == bytes32(0), "Response already recorded.");
        r.responseHash = _responseHash;
        r.responseTimestamp = block.timestamp;
    }

    function checkDeadline(uint256 _id) external {
        RTIRecord storage r = records[_id];
        require(r.filingTimestamp > 0, "Record not found.");
        if (!r.deadlineBreached && r.responseHash == bytes32(0)) {
            if (block.timestamp > r.filingTimestamp + DEADLINE_PERIOD) {
                r.deadlineBreached = true;
                emit DeadlineBreached(_id);
            }
        }
    }

    function updateAppealStatus(uint256 _id, uint8 _status) external {
        require(_status <= 3, "Invalid appeal status.");
        records[_id].appealStatus = _status;
        emit AppealStatusUpdated(_id, _status);
    }

    function getRecord(uint256 _id) external view returns (RTIRecord memory) {
        return records[_id];
    }
}
```

---

*End of Document — RTI-Lens PRD v2.0*
