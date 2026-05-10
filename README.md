# RTI-Lens: AI-Powered RTI Analytics Platform

**RTI-Lens** is an AI-powered platform for analyzing Right to Information (RTI) Act rulings in India. Uses **Hybrid RAG**, **Groq LLM inference**, and **Blockchain verification** for insights, predictions, and appeal drafting.

---

## 🚀 Key Features

### 1. **Hybrid RAG Pipeline**
- **BM25 (Lexical Search)** + **Semantic Vector Search** for case retrieval
- **MongoDB with sentence-transformers** (all-MiniLM-L6-v2) for semantic similarity
- **In-memory cosine similarity** computation for vector matching
- **PageIndex Verification Layer** for hierarchical context validation
- **Groq Llama 3.1-8b-instant** for fast, cost-effective inference

### 2. **AI-Powered Appeal Drafting**
- **Groq-based LLM generation** with structured JSON output
- **Section-specific statistics** to identify misuse patterns
- **Case precedent grounding** to prevent hallucinations
- **Change tracking** showing original vs improved query phrases
- **Avoid-phrase suggestions** based on denial patterns

### 3. **Predictive Analytics**
- **XGBoost-based outcome prediction** (Allowed/Denied/Partially Allowed)
- **Ministry-level misuse detection** using section citation patterns
- **Interactive knowledge graph** visualization of case relationships
- **Section statistics** with overturn rates

### 4. **Blockchain Integrity Layer**
- **Solana SPL Memo Program** for immutable RTI submission anchoring
- **SHA-256 document hashing** for tamper-proof verification
- **Citizen wallet history** for transparency
- **Simulation mode** fallback when private key unavailable
- **Devnet deployment** with explorer integration

### 5. **Voice-Enabled Interface**
- **ElevenLabs Speech-to-Text** for voice-based RTI queries
- **Groq Whisper** fallback for cost-effective transcription
- **Text-to-Speech** for accessibility

### 6. **Workflow Observability**
- **Backboard.io integration** for session management
- **Stage tracking** (retrieval → generation)
- **Thread-based session logging**
- **Retrieval and generation event logging**

---

## 🏗️ Architecture

> **📖 [View Detailed Architecture Documentation](./docs/ARCHITECTURE.md)** - Comprehensive diagrams, data flows, and technical specifications

### System Overview

```mermaid
graph TB
    subgraph "Frontend"
        UI[React 19 + Vite<br/>TailwindCSS]
    end

    subgraph "Backend APIs"
        QA[Q&A API]
        DRAFT[Draft API]
        PRED[Predict API]
        GRAPH[Graph API]
        BC[Blockchain API]
    end

    subgraph "Core Pipeline"
        RAG[Hybrid RAG<br/>BM25 + Semantic]
        PI[PageIndex<br/>Verification]
        LLM[Groq LLM<br/>Llama 3.1-8b]
        ML[XGBoost Model]
    end

    subgraph "Data Layer"
        PG[(PostgreSQL<br/>Cases & Paragraphs)]
        MDB[(MongoDB<br/>Vector Store)]
    end

    subgraph "External"
        GROQ[Groq API]
        SOL[Solana Devnet]
        BB[Backboard.io]
    end

    UI --> QA
    UI --> DRAFT
    UI --> PRED
    UI --> GRAPH
    UI --> BC

    QA --> RAG
    DRAFT --> RAG
    PRED --> ML
    GRAPH --> PG
    BC --> SOL

    RAG --> PG
    RAG --> MDB
    RAG --> PI
    PI --> PG
    PI --> LLM
    LLM --> GROQ
    ML --> PG
    QA --> BB
    DRAFT --> BB

    style RAG fill:#9333ea,stroke:#7c3aed,color:#fff
    style PI fill:#10b981,stroke:#059669,color:#fff
    style LLM fill:#00f3ff,stroke:#0099cc,color:#000
    style MDB fill:#47a248,stroke:#3d8b40,color:#fff
    style SOL fill:#14f195,stroke:#00d084,color:#000
    style BB fill:#f59e0b,stroke:#d97706,color:#000
```

### Hybrid RAG Pipeline

```mermaid
flowchart TD
    Q[User Query] --> PRE[Preprocessing]
    PRE --> BM25[BM25 Lexical Search<br/>rank-bm25]
    PRE --> VEC[Semantic Vector Search<br/>sentence-transformers]

    BM25 --> W1[Weight: 30%]
    VEC --> W2[Weight: 70%]

    W1 --> FUSE[Hybrid Score Fusion<br/>+ Structural Boost]
    W2 --> FUSE

    FUSE --> RANK[Relevance Ranking]
    RANK --> PI[PageIndex Verification<br/>Hierarchical Context]
    PI --> CTX[Context Assembly]

    CTX --> LLM[Groq LLM Generation<br/>Llama 3.1-8b-instant]
    Q --> LLM

    LLM --> RESP[Grounded Response<br/>+ Source Citations]

    style BM25 fill:#fbbf24,stroke:#f59e0b,color:#000
    style VEC fill:#8b5cf6,stroke:#7c3aed,color:#fff
    style LLM fill:#00f3ff,stroke:#0099cc,color:#000
    style PI fill:#10b981,stroke:#059669,color:#fff
```

### Blockchain Integration

```mermaid
flowchart LR
    DOC[RTI Document] --> HASH[SHA-256 Hash]
    HASH --> SPL[Solana SPL Memo<br/>Devnet]
    SPL --> TX[Transaction Signature]
    TX --> PROOF[Immutable Proof<br/>of Existence]

    style SPL fill:#14f195,stroke:#00d084,color:#000
    style PROOF fill:#10b981,stroke:#059669,color:#fff
```

---

## 🛠️ Tech Stack

### Backend
- **FastAPI** - High-performance async API framework
- **SQLAlchemy** - ORM for PostgreSQL
- **PostgreSQL** - Relational database for cases, paragraphs, ministries
- **MongoDB** - Document store for vector embeddings
- **sentence-transformers** - Embedding generation (all-MiniLM-L6-v2)
- **rank-bm25** - BM25 lexical search
- **Groq API** - LLM inference (Llama 3.1-8b-instant)
- **Backboard SDK** - Session management and workflow tracking
- **Solana.py** - Blockchain integration
- **ElevenLabs API** - Voice transcription and TTS

### Frontend
- **React 19** - UI framework
- **Vite** - Build tool
- **TailwindCSS** - Styling
- **shadcn/ui** - Component library
- **@solana/wallet-adapter** - Wallet integration
- **@xyflow/react** - Knowledge graph visualization
- **recharts** - Analytics charts

### ML/AI
- **scikit-learn** - XGBoost model training
- **pandas/numpy** - Data processing
- **spacy** - NLP entity extraction
- **nltk** - Text preprocessing

---

## 📦 Installation

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL 14+
- MongoDB 6+

### Backend Setup

```bash
cd IDP/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Configure environment
cp .env.example .env
# Edit .env with your API keys:
# - GROQ_API_KEY (required for Q&A and drafting)
# - OPENAI_API_KEY (optional, for embeddings)
# - BACKBOARD_API_KEY (optional, for session tracking)
# - ELEVENLABS_API_KEY (optional, for voice)
# - SOLANA_PRIVATE_KEY (optional, for blockchain writes)

# Run database migrations
alembic upgrade head

# Start server
python main.py
```

### Frontend Setup

```bash
cd IDP/frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

### MongoDB Setup

```bash
# Start MongoDB locally
mongod --dbpath /path/to/data

# Build embeddings (after loading cases into PostgreSQL)
cd IDP/backend
python scripts/build_embeddings.py
```

---

## 🔑 API Endpoints

### Q&A
```http
POST /api/qa
Content-Type: application/json

{
  "question": "What are common grounds for Section 8(1)(a) appeals?",
  "top_k": 5
}
```

### Appeal Drafting
```http
POST /api/draft
Content-Type: application/json

{
  "ministry": "Ministry of Home Affairs",
  "section_cited": "8(1)(a)",
  "context": "My RTI request about police records was denied..."
}
```

### Outcome Prediction
```http
POST /api/predict
Content-Type: application/json

{
  "ministry": "Ministry of Finance",
  "section_cited": "8(1)(d)",
  "appeal_level": "CIC"
}
```

### Blockchain Submission
```http
POST /api/blockchain/submit
Content-Type: multipart/form-data

wallet: <solana_wallet_address>
department: Ministry of Home Affairs
content: <RTI document text>
```

### Voice Transcription
```http
POST /api/voice/transcribe
Content-Type: multipart/form-data

file: <audio.wav>
```

---

## 📊 Data Pipeline

### 1. Case Ingestion
```bash
# Extract cases from PDF orders
python scripts/extract_cases.py --input data/orders/ --output data/cases.json

# Load into PostgreSQL
python scripts/load_cases.py --input data/cases.json
```

### 2. BM25 Index Building
```bash
# Build BM25 index from paragraphs
python scripts/build_bm25_index.py
# Output: data/bm25_pageindex.pkl
```

### 3. Vector Embeddings
```bash
# Generate embeddings and store in MongoDB
python scripts/build_embeddings.py
# Uses sentence-transformers to embed all paragraphs
```

### 4. PageIndex Creation
```bash
# Build hierarchical page index
python scripts/build_pageindex.py
# Output: data/pageindex.pkl
```

---

## 🧪 Testing

```bash
# Backend tests
cd IDP/backend
pytest tests/

# Frontend tests
cd IDP/frontend
npm run test
```

---

## 🚀 Deployment

### Backend (Docker)
```bash
cd IDP/backend
docker build -t rti-lens-backend .
docker run -p 8001:8001 --env-file .env rti-lens-backend
```

### Frontend (Vercel)
```bash
cd IDP/frontend
npm run build
vercel deploy
```

---

## 📈 Performance

- **Q&A Response Time**: ~2-3 seconds (including retrieval + LLM)
- **Draft Generation**: ~3-4 seconds
- **Prediction**: <100ms (XGBoost inference)
- **Voice Transcription**: ~1-2 seconds (ElevenLabs/Groq Whisper)
- **Blockchain Anchoring**: ~1-2 seconds (Solana devnet)

---

## 🔒 Security

- **Input Sanitization**: All user inputs sanitized against injection attacks
- **Rate Limiting**: 60 requests/minute per IP
- **Session Limits**: 20 Q&A calls per session
- **API Key Validation**: Format validation at startup
- **Blockchain Simulation**: Falls back to simulation mode if private key missing

---

## 📝 Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/rtilens
MONGODB_URI=mongodb://localhost:27017/

# AI APIs
GROQ_API_KEY=gsk_...
OPENAI_API_KEY=sk-...  # Optional
ELEVENLABS_API_KEY=sk_...  # Optional

# Workflow Tracking
BACKBOARD_API_KEY=espr_...  # Optional
BACKBOARD_ENABLED=true

# Blockchain
SOLANA_RPC_URL=https://api.devnet.solana.com
SOLANA_PRIVATE_KEY=[...]  # Optional, JSON array format

# Search Weights
BM25_WEIGHT=0.4
SEMANTIC_WEIGHT=0.6

# Models
EMBEDDING_MODEL=all-MiniLM-L6-v2
GROQ_MODEL=llama-3.1-8b-instant
```

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📄 License

MIT License - see LICENSE file for details

---

## 🙏 Acknowledgments

- **Central Information Commission (CIC)** for RTI order data
- **Groq** for fast LLM inference
- **Backboard.io** for workflow observability
- **Solana Foundation** for blockchain infrastructure
- **ElevenLabs** for voice AI capabilities
