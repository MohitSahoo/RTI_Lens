<div align="center">

<h1>
  <img src="https://img.shields.io/badge/🔍-RTI--Lens-6d28d9?style=flat-square&labelColor=1e1b4b" alt="RTI-Lens" />
</h1>

<p>
  <strong>AI-Powered RTI Analytics Platform for India</strong><br/>
  <em>Hybrid RAG · Multi-Agent LLMs · Blockchain · Voice · Workflow Observability</em>
</p>

<p>
  <a href="#"><img src="https://img.shields.io/badge/🏆%20NMIT%20HACKS%202026-MLH%20Track%20Prize%20(Backboard.io)-FFD700?style=for-the-badge&labelColor=1a1a2e" alt="MLH Prize"/></a>
</p>

<br/>

<p>
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white"/>
  <img src="https://img.shields.io/badge/React_19-20232A?style=for-the-badge&logo=react&logoColor=61DAFB"/>
  <img src="https://img.shields.io/badge/MongoDB_Atlas-47A248?style=for-the-badge&logo=mongodb&logoColor=white"/>
  <img src="https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white"/>
  <img src="https://img.shields.io/badge/Groq-F55036?style=for-the-badge&logo=groq&logoColor=white"/>
  <img src="https://img.shields.io/badge/Solana-9945FF?style=for-the-badge&logo=solana&logoColor=white"/>
  <img src="https://img.shields.io/badge/ElevenLabs-000000?style=for-the-badge&logo=elevenlabs&logoColor=white"/>
  <img src="https://img.shields.io/badge/Backboard.io-FF6B35?style=for-the-badge&logoColor=white"/>
  <img src="https://img.shields.io/badge/Gemini_Flash-4285F4?style=for-the-badge&logo=google&logoColor=white"/>
  <img src="https://img.shields.io/badge/Python_3.12-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript&logoColor=white"/>
  <img src="https://img.shields.io/badge/TailwindCSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white"/>
</p>

<br/>

> **RTI-Lens** is a full-stack AI platform that makes the Right to Information Act accessible to every Indian citizen —  
> with case-grounded answers, AI-drafted appeals, outcome predictions, and blockchain-verified submissions.

</div>

---

## 🏆 NMIT HACKS 2026 — MLH Track Prize Winner

<div align="center">

```
╔══════════════════════════════════════════════════════════════╗
║  🥇  WINNER — MLH Track Prize sponsored by Backboard.io    ║
║      NMIT HACKS 2026 Hackathon                              ║
║                                                              ║
║  Recognized for best production-grade integration of         ║
║  AI workflow observability in a civic-tech application.      ║
╚══════════════════════════════════════════════════════════════╝
```

</div>

RTI-Lens uses **Backboard.io** to create live-tracked workflow threads for every Q&A session and appeal draft, providing stage-by-stage audit trails across `initiated → retrieval → generation → completed`, stored in both Backboard's cloud and a local PostgreSQL audit table.

---

## 🗺️ System Architecture

```mermaid
graph TB
    subgraph FE["🖥️ Frontend  ·  React 19 + Vite + TailwindCSS"]
        UI_QA["❓ Q&A Interface"]
        UI_DRAFT["📝 Appeal Generator"]
        UI_PRED["📊 Predict Outcome"]
        UI_GRAPH["🕸️ Knowledge Graph"]
        UI_BC["⛓️ Blockchain Submit"]
        UI_VOICE["🎙️ Voice Input"]
    end

    subgraph PROXY["Vite Dev Proxy  :5173 → :8001"]
    end

    subgraph BE["⚡ Backend  ·  FastAPI + SQLAlchemy"]
        QA["/api/qa"]
        DRAFT["/api/draft"]
        PRED["/api/predict"]
        GRAPH["/api/graph"]
        BC["/api/blockchain"]
        VOICE["/api/voice"]
    end

    subgraph RAG["🔍 Hybrid RAG Pipeline"]
        BM25["📑 BM25 Lexical\nbm25_pageindex.pkl"]
        VEC["🧠 Semantic Vector\nall-MiniLM-L6-v2\n384-dim"]
        FUSE["⚖️ Score Fusion\nBM25 40% · Semantic 60%"]
        PI["🗂️ PageIndex Layer\nKeyword Boost + Diversity"]
        CTX["📄 Context Assembly"]
    end

    subgraph AGENTS["🤖 Multi-Agent Draft Pipeline"]
        A1["Groq Agent 1\nLegal Precision"]
        A2["Groq Agent 2\nStrategic Framing"]
        A3["Groq Agent 3\nCompleteness Check"]
        XGB["📉 XGBoost Scorer\nAllowed/Denied Prob"]
        GEM["✨ Gemini Flash\nOrchestrator"]
    end

    subgraph DATA["🗄️ Data Layer"]
        PG[("🐘 PostgreSQL\ncases · paragraphs\nministries · sessions")]
        MDB[("🍃 MongoDB Atlas\n5,251 vector chunks\n713 CIC documents")]
    end

    subgraph EXT["🌐 External Services"]
        GROQ["⚡ Groq API\nLlama 3.1-8b-instant\n3 rotating keys"]
        GEMINI["🔵 Google Gemini\nFlash 1.5"]
        EL["🎵 ElevenLabs\nScribe v1 STT\n+ TTS"]
        BB["📡 Backboard.io\nWorkflow Observability\n🏆 MLH Prize"]
        SOL["💜 Solana Devnet\nSPL Memo Anchoring"]
        RAGAS["📐 RAGAS\nFaithfulness\nContext Precision"]
    end

    UI_QA & UI_DRAFT & UI_PRED & UI_GRAPH & UI_BC & UI_VOICE --> PROXY
    PROXY --> QA & DRAFT & PRED & GRAPH & BC & VOICE

    QA --> BM25 & VEC
    DRAFT --> BM25 & VEC
    BM25 & VEC --> FUSE --> PI --> CTX
    CTX --> GROQ

    DRAFT --> A1 & A2 & A3
    A1 & A2 & A3 --> XGB --> GEM

    QA --> RAGAS
    QA & DRAFT --> BB

    PRED --> PG
    GRAPH --> PG
    QA & DRAFT --> PG
    VEC --> MDB
    BM25 --> PG

    GROQ --> A1 & A2 & A3
    GEM --> GEMINI
    BC --> SOL
    VOICE --> EL

    style BB fill:#FF6B35,stroke:#cc4a10,color:#fff
    style GEM fill:#4285F4,stroke:#1a56c4,color:#fff
    style GROQ fill:#F55036,stroke:#c22d17,color:#fff
    style MDB fill:#47A248,stroke:#2d7a2d,color:#fff
    style PG fill:#316192,stroke:#1a3f6b,color:#fff
    style SOL fill:#9945FF,stroke:#6b1fd1,color:#fff
    style EL fill:#000000,stroke:#444,color:#fff
    style RAGAS fill:#7c3aed,stroke:#5b21b6,color:#fff
    style PI fill:#059669,stroke:#047857,color:#fff
    style XGB fill:#f59e0b,stroke:#d97706,color:#000
```

---

## 🔄 Hybrid RAG Pipeline — Deep Dive

```mermaid
flowchart LR
    Q["🗣️ User Query"] --> PRE["🧹 Sanitize & Preprocess"]

    PRE --> B["📑 BM25 Search\nrank-bm25\ntop_k×3 candidates"]
    PRE --> V["🧠 Semantic Search\nMongoDB Atlas\nCosine Similarity"]

    B --> F["⚖️ Score Fusion\n40% BM25 + 60% Semantic\n+ Structural Boost"]
    V --> F

    F --> DEDUP["🔄 Deduplicate\nby order_number"]
    DEDUP --> PI["🗂️ PageIndex Layer\n• 500-word chunks + 100 overlap\n• Keyword & section citation boost\n• Max 2 chunks per document"]
    PI --> CTX["📚 Context Assembly\n[Source N] Order: ...\nSection: ...\nText: ..."]

    CTX --> LLM["⚡ Groq Llama 3.1-8b\nGrounded Answer\n+ Source Citations"]
    Q --> LLM

    LLM --> EVAL["📐 RAGAS Evaluation\nFaithfulness\nContext Precision\nContext Recall"]
    EVAL --> RESP["✅ Final Response\n+ Confidence Score\n+ Thread ID (Backboard)"]

    style PI fill:#059669,stroke:#047857,color:#fff
    style LLM fill:#F55036,stroke:#c22d17,color:#fff
    style EVAL fill:#7c3aed,stroke:#5b21b6,color:#fff
    style F fill:#f59e0b,stroke:#d97706,color:#000
```

---

## 🤖 Multi-Agent Appeal Draft Pipeline

```mermaid
sequenceDiagram
    actor User
    participant API as FastAPI /api/draft
    participant BB as Backboard.io 🏆
    participant RAG as Hybrid RAG
    participant G1 as Groq Agent 1<br/>(Legal Precision)
    participant G2 as Groq Agent 2<br/>(Strategic)
    participant G3 as Groq Agent 3<br/>(Comprehensive)
    participant XGB as XGBoost Model
    participant GEM as Gemini Flash<br/>(Orchestrator)

    User->>API: POST /api/draft {context, ministry, section}
    API->>BB: create_workflow_session("rti_draft")
    BB-->>API: thread_id
    API->>RAG: retrieve_precedents(query, top_k=10)
    RAG-->>API: 5 precedent cases
    API->>BB: log_retrieval(thread_id, method, count)

    par Parallel Agent Execution
        API->>G1: legal_precision_prompt
        API->>G2: strategic_framing_prompt
        API->>G3: comprehensive_review_prompt
    end

    G1-->>XGB: draft_text
    G2-->>XGB: draft_text
    G3-->>XGB: draft_text

    XGB-->>GEM: scored_results (allowed/denied prob)
    API->>GEM: orchestrate(accepted_drafts, precedents)
    GEM-->>API: final_draft + change_notes + avoid_phrases

    API->>BB: update_stage("completed")
    API-->>User: DraftResponse {draft, sources, pipeline_trace}
```

---

## 📦 Quick Start

### Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.12+ |
| Node.js | 18+ |
| PostgreSQL | 14+ |
| MongoDB Atlas | Cloud cluster |

### 1. Clone & Setup

```bash
git clone https://github.com/yourorg/RTI_Lens.git
cd RTI_Lens

# Backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Frontend
cd frontend && npm install
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your credentials (see table below)
```

<details>
<summary>📋 <strong>Full Environment Variable Reference</strong></summary>

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | ✅ | PostgreSQL connection string |
| `MONGODB_URI` | ✅ | MongoDB Atlas connection URI |
| `GROQ_API_KEY` | ✅ | Primary Groq API key |
| `GROQ_API_KEY_1/2/3` | ✅ | Rotating keys for 3 parallel agents |
| `GEMINI_API_KEY` | ✅ | Google AI API key for orchestration |
| `ELEVENLABS_API_KEY` | ✅ | ElevenLabs STT + TTS |
| `BACKBOARD_API_KEY` | ✅ | Backboard.io workflow observability |
| `SOLANA_PRIVATE_KEY` | ⚠️ | JSON array — falls back to simulation if absent |
| `SOLANA_RPC_URL` | ⚪ | Defaults to `https://api.devnet.solana.com` |
| `BM25_WEIGHT` | ⚪ | Defaults to `0.4` |
| `SEMANTIC_WEIGHT` | ⚪ | Defaults to `0.6` |
| `EMBEDDING_MODEL` | ⚪ | Defaults to `all-MiniLM-L6-v2` |
| `GROQ_MODEL` | ⚪ | Defaults to `llama-3.1-8b-instant` |
| `GEMINI_MODEL` | ⚪ | Defaults to `gemini-1.5-flash` |

</details>

### 3. Data Ingestion (First-time)

```bash
python step1_ingest_postgres.py       # Load cases → PostgreSQL
python step2_create_markdown_mongodb.py  # Create markdown + MongoDB docs
python step3_build_pageindex.py       # Build hierarchical index trees
python step4_build_bm25.py            # Build BM25 lexical index
python step5_build_embeddings.py      # Embed all docs → MongoDB Atlas
                                      # ⏱ ~2 min · 713 docs · 5,251 chunks
```

### 4. Run

```bash
# Terminal 1 — Backend
source .venv/bin/activate
uvicorn backend.main:app --host 127.0.0.1 --port 8001

# Terminal 2 — Frontend
cd frontend && npm run dev
# → http://localhost:5173
```

---

## 🔌 API Reference

<details>
<summary>📡 <strong>All Endpoints</strong></summary>

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | System health + BM25/PageIndex status |
| `POST` | `/api/qa` | Hybrid RAG Q&A with RAGAS evaluation |
| `POST` | `/api/draft` | Multi-agent appeal draft generation |
| `POST` | `/api/predict` | XGBoost outcome prediction |
| `GET` | `/api/analytics/sections` | Section-level denial statistics |
| `GET` | `/api/analytics/ministries` | Ministry-level trend data |
| `GET` | `/api/graph` | Knowledge graph nodes + edges |
| `GET` | `/api/dashboard/stats` | Summary dashboard stats |
| `POST` | `/api/blockchain/submit` | Anchor RTI document on Solana |
| `GET` | `/api/blockchain/history` | Wallet submission history |
| `POST` | `/api/voice/transcribe` | STT: ElevenLabs → Groq Whisper fallback |
| `POST` | `/api/voice/speak` | TTS via ElevenLabs Rachel voice |
| `GET` | `/api/query-assistant/suggestions` | RTI query optimization |
| `GET` | `/api/qa/source` | Full PageIndex context for order number |

</details>

---

## 📊 Corpus & Performance

<div align="center">

| Metric | Value |
|--------|-------|
| 📄 CIC Court Orders | 713 documents |
| 🧩 Vector Chunks | 5,251 (avg 7.4/doc) |
| 📐 Chunk Strategy | 500 words / 100 overlap |
| 🔢 Embedding Dimensions | 384 (all-MiniLM-L6-v2) |
| ⚡ Q&A Latency | ~2–3 seconds |
| 📝 Draft Generation | ~6–10 seconds |
| 🎯 Outcome Prediction | <100ms |
| 🎙️ Voice Transcription | ~1–2 seconds |
| ⛓️ Blockchain Anchor | ~1–2 seconds (Devnet) |
| 🔒 Rate Limit | 60 req/min per IP |
| 🔄 Session Limit | 20 Q&A calls/session |

</div>

---

## 📡 Backboard.io Integration (MLH Prize Winner 🏆)

Every user interaction creates a fully tracked workflow thread:

```
Session Created   → Backboard thread_id assigned
      │
      ▼
Stage: retrieval  → log_retrieval(query, method, num_results, top_sources)
      │
      ▼
Stage: generation → log_generation(prompt_type, response_summary, model)
      │
      ▼
Stage: completed  → update_workflow_state("completed")
```

All events are mirrored to **PostgreSQL** `workflow_sessions` and `workflow_actions` tables for local audit trails, independent of Backboard's availability.

---

## 🛡️ Security

- ✅ Input sanitization on all endpoints
- ✅ SlowAPI rate limiting (60 req/min per IP)
- ✅ Session Q&A cap (20 calls/session)
- ✅ XGBoost model loaded with SHA-256 hash verification
- ✅ Blockchain simulation fallback when private key absent
- ✅ CORS configured for local development origins

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

Built with ❤️ for Indian citizens exercising their right to information.

<br/>

<img src="https://img.shields.io/badge/Made%20in-India%20🇮🇳-FF9933?style=for-the-badge"/>
<img src="https://img.shields.io/badge/Powered%20by-Groq%20⚡-F55036?style=for-the-badge"/>
<img src="https://img.shields.io/badge/Observability-Backboard.io%20🏆-FF6B35?style=for-the-badge"/>

</div>
