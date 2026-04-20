# 👁️ RTI-Lens: Intelligent CIC Order Analytics

**An AI-Powered Platform for the Central Information Commission (CIC)**

[![Status: v2.0 In Progress](https://img.shields.io/badge/Status-v2.0%20In%20Progress-yellow.svg)](#)
[![Backend: Production Ready](https://img.shields.io/badge/Backend-Production%20Ready-success.svg)](#)
[![AI Engine: Gemini RAG](https://img.shields.io/badge/AI-Google%20Gemini-orange.svg)](#)
[![CI/CD: GitHub Actions](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-blue.svg)](#)

---

## 📋 Table of Contents
1. [Platform Overview](#-platform-overview)
2. [Product Goals](#-product-goals)
3. [What Was Built v1.0 (Backend)](#-what-was-built-v10)
4. [v2.0 Roadmap (In Progress)](#-v20-roadmap)
5. [Key Project Statistics](#-key-project-statistics)
6. [System Architecture](#-system-architecture)
7. [Data Pipeline Detail](#-data-pipeline-detail)
8. [API Catalog](#-api-catalog)
9. [Quick Start Guide](#-quick-start-guide)
10. [Database Schema](#-database-schema)
11. [Documentation](#-documentation)

---

## 🎯 Platform Overview

RTI-Lens is a comprehensive platform engineered for parsing, analyzing, and interrogating India's Right to Information (RTI) Act rulings adjudicated by the Central Information Commission (CIC). By uniting **traditional Machine Learning (Random Forests)** with Next-Gen Generative AI through **Retrieval-Augmented Generation (RAG)** leveraging Google Gemini, it empowers citizens and legal experts alike to understand legal precedents instantly without reading hundreds of convoluted PDFs.

The engine can predict whether an appeal will be allowed or denied, highlight specific ministries misusing legal provisions, rapidly retrieve relevant case sections, and draft professional legal appeals automatically.

---

## 🏆 Product Goals

| # | Goal | Measurable Outcome | Status |
|---|------|--------------------|----|
| G1 | Expose denial patterns per ministry and Section 8 clause | Ministry Denial Score for every ministry with ≥5 orders | ✅ Backend complete |
| G2 | Grounded, cited answers from CIC precedents | Q&A with BM25 + PageIndex + faithfulness check | ✅ Backend complete |
| G3 | Help citizens draft RTI queries less likely to be denied | LLM reformulation with precedent citations | ✅ Backend complete |
| G4 | Predict appeal success probability | ML classifier F1 = 0.81 | ✅ Backend complete |
| G5 | Tamper-proof RTI filing via blockchain | RTIRecord contract on Polygon testnet | 🔲 Planned |

---

## 🚀 What Was Built v1.0

### 1. Robust Data Processing & ETL Pipeline
We replaced the need to manually read CIC files by converting 712 raw unformatted TXT case files into highly structured PostgreSQL representations via Python algorithms targeting Regular Expressions (`re`) and NLP (`spaCy`).

### 2. Hierarchical Retrieval Engine
Instead of relying strictly on flat keyword search, we deployed a custom implementation of **VectifyAI's PageIndex**. We parse standard CIC text formats into markdown, extract headers recursively, and construct JSON representation trees of every single order. This allows our Q&A pipeline to isolate "Commission Findings" explicitly without confusing it with the initial "Information Sought."

### 3. Machine Learning Predictor
Trained a Scikit-Learn `RandomForestClassifier` utilizing TF-IDF embeddings concatenated with Scaled temporal identifiers.
- Determines historical likelihood of a case being won based purely on text, section cited, and ministry.

### 4. Zero-Trust Generative Q&A
Employs Google Gemini (`gemini-flash-lite-latest`) combined with a two-step agentic validation pass:
1. Agent answers user question leveraging context from the BM25/PageIndex pipeline.
2. The agent verifies its own response to enforce "faithfulness" back to the underlying retrieved CIC source document, virtually eliminating hallucinations.

### 5. High-Performance Server
Powered by an asynchronous **FastAPI** web framework incorporating native HTTP rate limiting (`slowapi`) preventing AI abuse via in-memory Session tracking.

---

## 🗺️ v2.0 Roadmap

v2.0 enhances the backend infrastructure and builds the complete user-facing product:

| Phase | Description | Key Technology | Status |
|-------|-------------|---------------|--------|
| **A** | Replace raw SQL with typed ORM | Prisma Client Python | 🔲 Planned |
| **B** | Add flexible GraphQL API layer | Strawberry GraphQL | 🔲 Planned |
| **C** | Containerize + CI/CD automation | Docker + GitHub Actions | 🔲 Planned |
| **D** | Build 4-page React frontend | React 18 + Vite + Tailwind + Recharts | 🔲 Planned |
| **E** | Blockchain RTI filing | Solidity + web3.py + Polygon Mumbai | 🔲 Planned |

> Full details: [docs/implementation_plan.md](docs/implementation_plan.md) | Task tracker: [docs/task.md](docs/task.md) | Workflow guide: [docs/workflow.md](docs/workflow.md)

---

## 📊 Key Project Statistics

| Metric | Measured Value |
|--------|-------|
| **Total Sources Processed** | 712 raw Orders |
| **Cases Normalized** | 469 mapped objects |
| **Actionable Paragraphs** | 43,151 snippets |
| **BM25 Search Index Size** | 26 MB Singleton |
| **ML Predictor Setup** | RandomForest (81.25% Acc, 0.81 F1) |
| **Python Backend Scope** | 12 optimized micro-modules |

**Noteworthy Policy Insights Found:**
- The **Ministry of Corporate Affairs** faces an ~80% appeal defeat probability historically.
- The **Ministry of Finance** holds one of the strongest defensive postures, denying with only ~30% overturn likelihood.

---

## 🏗️ System Architecture

Our Data and inference pipeline isolates expensive retrieval steps in-memory across singletons whilst delegating transactional actions directly to PostgreSQL.

```mermaid
flowchart TD
    subgraph Data Layer
        TXT["Raw TXT Orders"] --> ETL["ingest.py"]
        ETL --> DB[(PostgreSQL)]
        DB --> BM25["build_bm25.py"]
        BM25 -.-> IDX[("bm25_pageindex.pkl\n(Singleton)")]
        TXT --> MD["txt_to_markdown.py"]
        MD --> PI["build_pageindex.py"]
        PI -.-> TREE[("JSON Trees\n(Singleton)")]
    end

    subgraph FastAPI Core
        API["FastAPI Web Server"]
        API --> Stats["Analytics\nRouters"]
        API --> RAG["Q&A + Draft\nRouters"]
        Stats --> DB
        RAG --> IDX
        RAG --> TREE
        RAG <==> Gem["Google Gemini\nLLM"]
    end
```

---

## ⚙️ Data Pipeline Detail

If setting up the infrastructure from scratch, scripts must be run in exact order to build the artifacts properly:

1. **`scripts/ingest.py`**: Reads raw CIC formats and populates the database `cases` table.
2. **`scripts/compute_stats.py`**: Executes aggregations into `ministry_stats` and `section_stats`.
3. **`scripts/build_bm25.py`**: Maps paragraphs into an optimized search space.
4. **`scripts/train_classifier.py`**: Outputs the ML model logic as a `.pkl`.
5. **`scripts/txt_to_markdown.py` → `scripts/build_pageindex.py`**: Builds formatting structures enabling the RAG system to comprehend sections accurately.
6. **`scripts/build_order_mapping.py`**: Creates order number → file hash mapping for PageIndex lookups.
7. **`scripts/build_knowledge_graph.py`**: Constructs the ministry → section → outcome knowledge graph.

---

## 🔌 API Catalog

**API Base**: `http://localhost:8001`
**Swagger Docs Built-in**: `http://localhost:8001/docs`
**GraphQL Playground**: `http://localhost:8001/graphql` *(v2.0)*

| Method | Route | Auth Req | Purpose |
|--------|-------|----------|---------|
| **GET** | `/health` | No | Heartbeat + service injection status |
| **GET** | `/api/analytics/denial-rates` | No | Ministry denial rates sorted by index |
| **GET** | `/api/analytics/section-heatmap` | No | Section citation overturned frequencies |
| **GET** | `/api/analytics/override-trend` | No | Temporal override rate moving average |
| **GET** | `/api/analytics/ministry/{id}/orders` | No | Paginated orders for a specific ministry |
| **POST**| `/api/predict` | No | `{ "ministry": "...", "section_cited": "8(1)(j)", "raw_text": "..." }` |
| **POST**| `/api/qa` | **Gemini Key** | `{ "question": "Why is 8(1)(j) normally overturned here?" }` |
| **POST**| `/api/draft` | **Gemini Key** | RTI appeal drafts citing CIC precedents |
| **GET** | `/api/graph` | No | Knowledge graph (nodes + edges) |

---

## 🏁 Quick Start Guide

**1. Clone and Configure**
Ensure Python 3.11+ and PostgreSQL 14+ is installed.
```bash
# Add your Gemini Key
echo "GEMINI_API_KEY=AIzaSy_YOUR_KEY_HERE" >> .env
# Optional DB Config
echo "DATABASE_URL=postgresql://user@localhost:5432/rtilens" >> .env
```

**2. Provision Environment**
```bash
pip install -r requirements.txt
# Ensure PostgreSQL is actively running
brew services start postgresql@14
```

**3. Run Diagnostic Check**
```bash
chmod +x validate.sh
./validate.sh
```

**4. Start Server Operations**
```bash
python3 backend/main.py
# API available at http://localhost:8001
# Swagger docs at http://localhost:8001/docs
```

**5. Run Tests** *(v2.0)*
```bash
python3 test_api.py          # Manual smoke tests
pytest tests/ -v --tb=short  # Automated test suite (after Phase C)
```

---

## 🗄️ Database Schema

The implementation is backed by a fully normalized `Postgres` structure utilizing `TIMESTAMPTZ` and associative mapping:

- **`ministries`**: Resolves arbitrary entity naming mismatches inside source texts.
- **`cases`**: Base truth containing canonical `order_url`, `section_cited`, `appeal_outcome` and temporal tracking.
- **`paragraphs`**: Bound via Cascading Foreign Key back to the individual case; required for granular spatial vector mapping.
- **`ministry_stats` / `section_stats`**: High-performance Cached aggregates queried natively by the FastAPI analytics interfaces.
- **`blockchain_filings`**: Architecture for storing cryptographic timestamps of rulings against tamper attempts.

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| [RTI_Lens_PRD.md](RTI_Lens_PRD.md) | Full product requirements document (v2.0) |
| [docs/workflow.md](docs/workflow.md) | Developer & Agent workflow guide |
| [docs/implementation_plan.md](docs/implementation_plan.md) | v2.0 architecture & implementation plan |
| [docs/task.md](docs/task.md) | Project task tracker with progress |
| [BACKEND_AUDIT_REPORT.md](BACKEND_AUDIT_REPORT.md) | Backend security & quality audit |
