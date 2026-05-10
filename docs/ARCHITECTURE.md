# RTI-Lens System Architecture

## High-Level Architecture

```mermaid
graph TB
    subgraph "Frontend Layer"
        UI[React + TypeScript UI]
        QA[Q&A Interface]
        AG[Appeal Generator]
        PR[Predictor Dashboard]
        KG[Knowledge Graph]
        BC[Blockchain Tracker]
    end

    subgraph "API Gateway"
        API[FastAPI Backend]
    end

    subgraph "Core Services"
        QAS[Query Assistant Service]
        RAG[Hybrid RAG Engine]
        DG[Draft Generator]
        ML[XGBoost Predictor]
        GS[Graph Service]
    end

    subgraph "Data Layer"
        MDB[(MongoDB Vector Store)]
        PG[(PostgreSQL)]
        BM25[BM25 Index]
        VEC[Sentence Transformers]
    end

    subgraph "External Services"
        GROQ[Groq API<br/>Llama 3.1-8b-instant]
        SOL[Solana Blockchain<br/>SPL Memo Program]
        PI[PageIndex Verification]
    end

    UI --> API
    QA --> API
    AG --> API
    PR --> API
    KG --> API
    BC --> API

    API --> QAS
    API --> RAG
    API --> DG
    API --> ML
    API --> GS

    QAS --> RAG
    QAS --> GROQ
    DG --> RAG
    DG --> GROQ
    RAG --> MDB
    RAG --> BM25
    RAG --> VEC
    RAG --> PI
    ML --> PG
    GS --> PG
    BC --> SOL

    style GROQ fill:#00f3ff,stroke:#0099cc,color:#000
    style RAG fill:#9333ea,stroke:#7c3aed,color:#fff
    style MDB fill:#47a248,stroke:#3d8b40,color:#fff
    style SOL fill:#14f195,stroke:#00d084,color:#000
```

## Detailed Service Architecture

```mermaid
graph LR
    subgraph "Appeal Generation Pipeline"
        A1[User Query Input] --> A2[Query Assistant]
        A2 --> A3[Weakness Detection]
        A2 --> A4[Metadata Extraction]
        A2 --> A5[Hybrid RAG Retrieval]
        
        A5 --> A6[BM25 Lexical Search]
        A5 --> A7[Semantic Vector Search]
        A6 --> A8[Hybrid Scoring]
        A7 --> A8
        
        A8 --> A9[Precedent Ranking]
        A9 --> A10[Groq LLM Generation]
        A4 --> A10
        A3 --> A10
        
        A10 --> A11[Structured Draft Output]
        A11 --> A12[Blockchain Anchoring]
    end

    style A5 fill:#9333ea,stroke:#7c3aed,color:#fff
    style A10 fill:#00f3ff,stroke:#0099cc,color:#000
    style A12 fill:#14f195,stroke:#00d084,color:#000
```

## RAG Pipeline Detail

```mermaid
flowchart TD
    Q[User Question] --> QP[Query Preprocessing]
    QP --> HS[Hybrid Search]
    
    HS --> BM25S[BM25 Search<br/>70k+ paragraphs]
    HS --> VS[Vector Search<br/>MongoDB Atlas]
    
    BM25S --> W1[Weight: 0.3]
    VS --> W2[Weight: 0.7]
    
    W1 --> COMB[Hybrid Combiner]
    W2 --> COMB
    
    COMB --> RANK[Relevance Ranking]
    RANK --> FILT[Min Score Filter]
    FILT --> TOP[Top-K Selection]
    
    TOP --> PV[PageIndex Verification]
    PV --> CTX[Context Assembly]
    
    CTX --> LLM[Groq LLM<br/>Llama 3.1-8b-instant]
    Q --> LLM
    
    LLM --> ANS[Grounded Answer]
    ANS --> CONF[Confidence Scoring]
    CONF --> OUT[Response + Sources]

    style BM25S fill:#fbbf24,stroke:#f59e0b,color:#000
    style VS fill:#8b5cf6,stroke:#7c3aed,color:#fff
    style LLM fill:#00f3ff,stroke:#0099cc,color:#000
    style PV fill:#10b981,stroke:#059669,color:#fff
```

## Data Flow: Appeal Generation

```mermaid
sequenceDiagram
    participant U as User
    participant FE as Frontend
    participant API as FastAPI
    participant QA as Query Assistant
    participant RAG as Hybrid RAG
    participant DB as MongoDB
    participant LLM as Groq API
    participant BC as Solana

    U->>FE: Submit RTI Query
    FE->>API: POST /api/query-assistant/optimize
    API->>QA: Analyze Query
    
    QA->>QA: Detect Weaknesses
    QA->>QA: Extract Metadata
    QA->>RAG: Retrieve Precedents
    
    RAG->>DB: BM25 + Vector Search
    DB-->>RAG: Ranked Results
    RAG->>RAG: Hybrid Scoring
    RAG-->>QA: Top Precedents
    
    QA-->>API: Optimization Result
    API-->>FE: Ministry + Section Suggestions
    
    FE->>API: POST /api/draft
    API->>LLM: Generate Draft (with precedents)
    LLM-->>API: Structured Draft
    
    API->>BC: Anchor Transaction
    BC-->>API: TX Signature
    
    API-->>FE: Final Draft + TX
    FE-->>U: Display Result
```

## Technology Stack

```mermaid
mindmap
  root((RTI-Lens))
    Frontend
      React 19
      TypeScript
      Vite
      TailwindCSS
      Framer Motion
      React Flow
    Backend
      FastAPI
      Python 3.11+
      Pydantic
      Uvicorn
    AI/ML
      Groq API
        Llama 3.1-8b-instant
      Sentence Transformers
        all-MiniLM-L6-v2
      XGBoost
      PageIndex
    Data
      MongoDB Atlas
        Vector Search
      PostgreSQL
        Structured Data
      BM25 Index
        In-Memory
    Blockchain
      Solana
        SPL Memo Program
      Web3.js
```

## Deployment Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        B[Browser]
    end

    subgraph "Application Layer"
        FE[Frontend Server<br/>Vite/Nginx]
        BE[Backend Server<br/>FastAPI/Uvicorn]
    end

    subgraph "Data Layer"
        MDB[(MongoDB Atlas<br/>Vector Store)]
        PG[(PostgreSQL<br/>Relational Data)]
    end

    subgraph "External APIs"
        GROQ[Groq Cloud API]
        SOL[Solana Mainnet]
    end

    B -->|HTTPS| FE
    FE -->|REST API| BE
    BE -->|Query| MDB
    BE -->|Query| PG
    BE -->|LLM Calls| GROQ
    BE -->|Transactions| SOL

    style FE fill:#0ea5e9,stroke:#0284c7,color:#fff
    style BE fill:#8b5cf6,stroke:#7c3aed,color:#fff
    style MDB fill:#47a248,stroke:#3d8b40,color:#fff
    style PG fill:#336791,stroke:#2d5a7b,color:#fff
    style GROQ fill:#00f3ff,stroke:#0099cc,color:#000
    style SOL fill:#14f195,stroke:#00d084,color:#000
```

## Key Components

### 1. Hybrid RAG Engine
- **BM25 Lexical Search**: Keyword-based retrieval for exact term matching
- **Semantic Vector Search**: MongoDB Atlas vector search with sentence-transformers
- **Hybrid Scoring**: Weighted combination (30% BM25, 70% semantic)
- **PageIndex Verification**: Hierarchical context validation

### 2. Query Assistant
- **Weakness Detector**: Identifies vague wording, missing dates, emotional language
- **Metadata Extractor**: Extracts dates, ministries, document types
- **Precedent Retriever**: Uses hybrid RAG to find relevant CIC cases
- **Query Rewriter**: Groq-based LLM rewriting with structured prompts

### 3. Draft Generator
- **Context Assembly**: Combines user input, precedents, and statistics
- **LLM Generation**: Groq Llama 3.1-8b-instant for structured output
- **Change Tracking**: Documents improvements made to original query
- **Blockchain Anchoring**: Solana SPL Memo for immutable audit trail

### 4. Predictive Analytics
- **XGBoost Model**: Trained on 10,000+ historical rulings
- **Feature Engineering**: Ministry, section, query characteristics
- **Outcome Prediction**: Allowed/Denied/Partially Allowed
- **Confidence Scoring**: Probability distribution across outcomes

### 5. Knowledge Graph
- **Entity Extraction**: Ministries, sections, outcomes
- **Relationship Mapping**: Case-to-case connections
- **Interactive Visualization**: React Flow with Dagre layout
- **Statistical Insights**: Section usage patterns, overturn rates

## Performance Characteristics

| Component | Latency | Throughput |
|-----------|---------|------------|
| Hybrid RAG Search | ~200ms | 50 req/s |
| Groq LLM Generation | ~2-4s | 10 req/s |
| XGBoost Prediction | ~50ms | 100 req/s |
| MongoDB Vector Search | ~150ms | 60 req/s |
| BM25 Search | ~30ms | 200 req/s |

## Security & Compliance

```mermaid
graph LR
    subgraph "Security Layers"
        A[Input Validation] --> B[API Authentication]
        B --> C[Rate Limiting]
        C --> D[Data Encryption]
        D --> E[Audit Logging]
        E --> F[Blockchain Verification]
    end

    style A fill:#ef4444,stroke:#dc2626,color:#fff
    style F fill:#14f195,stroke:#00d084,color:#000
```

- **Input Validation**: Pydantic schemas for all API endpoints
- **Rate Limiting**: Per-IP throttling on expensive operations
- **Data Encryption**: TLS 1.3 for all external communication
- **Audit Logging**: Blockchain-anchored transaction records
- **Secret Management**: Environment-based configuration, no hardcoded keys

## Scalability Considerations

1. **Horizontal Scaling**: Stateless FastAPI backend supports multiple instances
2. **Caching**: In-memory BM25 index for fast lexical search
3. **Database Indexing**: MongoDB vector indexes, PostgreSQL B-tree indexes
4. **Async Operations**: FastAPI async endpoints for I/O-bound operations
5. **CDN**: Static frontend assets served via CDN

## Future Enhancements

- [ ] Multi-language support (Hindi, regional languages)
- [ ] Real-time collaboration on draft editing
- [ ] Advanced analytics dashboard with time-series predictions
- [ ] Integration with government RTI portals
- [ ] Mobile application (React Native)
- [ ] Voice-to-text RTI query submission
- [ ] Automated appeal filing workflow
