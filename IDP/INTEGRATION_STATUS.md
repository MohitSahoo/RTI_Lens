# Frontend-Backend Integration Status Report

**Date**: 2026-05-09  
**Status**: ⚠️ PARTIALLY INTEGRATED - Backend Running, Data Missing

---

## ✅ Completed Work

### 1. Backend Server
- **Status**: ✅ Running on port 8002
- **Framework**: FastAPI with SQLAlchemy ORM
- **Modifications Made**:
  - Disabled GraphQL (strawberry dependency issue)
  - Made vector search optional (PyTorch DLL issues on Windows)
  - Made Backboard client optional (missing dependency)
  - Updated CORS to allow frontend (localhost:5173)
  - Changed port from 8001 to 8002 (.env updated)

**Backend Logs**:
```
INFO: Uvicorn running on http://0.0.0.0:8002
WARNING: Vector search unavailable (PyTorch DLL error)
INFO: Application startup complete
```

### 2. Frontend API Service Layer
Created complete API integration layer:

**Files Created**:
- `frontend/src/services/api.ts` - API client with all endpoints
- `frontend/src/hooks/useAPI.ts` - React hooks for API calls

**API Client Features**:
- TypeScript types for all requests/responses
- Error handling
- Automatic JSON parsing
- Support for all backend endpoints:
  - Q&A (`/api/qa`)
  - Prediction (`/api/predict`)
  - Draft Generation (`/api/draft`)
  - Analytics (denial rates, heatmap, trends)
  - Dashboard stats

**React Hooks**:
- `useQA()` - Q&A with loading/error states
- `usePredict()` - Outcome prediction
- `useDraft()` - Draft generation
- `useAnalytics()` - Analytics data fetching

### 3. Vite Configuration
- **Updated**: `frontend/vite.config.ts`
- **Proxy**: `/api` → `http://localhost:8002`
- Frontend dev server will proxy all API calls to backend

---

## ⚠️ Current Issues

### Backend Data Missing
The backend is running but **all endpoints fail** due to missing data:

```bash
# Health Check Result:
{
  "status": "unhealthy",
  "error": "BM25 index not found at data\\bm25_pageindex.pkl",
  "orm_mode": true
}
```

**Missing Components**:
1. **Database**: No cases in database (SQLite at `./rtilens.db`)
2. **BM25 Index**: `data/bm25_pageindex.pkl` doesn't exist
3. **PageIndex**: PageIndex data not built
4. **ML Model**: `data/model.pkl` not found
5. **Knowledge Graph**: `data/knowledge_graph.pkl` not found

**Required Setup Steps** (from project docs):
```bash
# Step 1: Ingest data to PostgreSQL/SQLite
python step1_ingest_postgres.py

# Step 2: Create markdown in MongoDB
python step2_create_markdown_mongodb.py

# Step 3: Build PageIndex
python step3_build_pageindex.py

# Step 4: Build BM25 index
python step4_build_bm25.py

# Step 5: Build embeddings
python step5_build_embeddings.py
```

### Frontend Components Not Integrated
All frontend components still use **mock data**:

| Component | Status | Issue |
|-----------|--------|-------|
| `AIQA.tsx` | ❌ Mock | Uses `setTimeout()` to simulate responses |
| `Predictor.tsx` | ❌ Mock | Hardcoded radar chart data |
| `Analytics.tsx` | ❌ Mock | Static ministry/clause data |
| `AppealGenerator.tsx` | ❌ Mock | Fake draft generation |
| `KnowledgeGraph.tsx` | ❌ Not checked | Likely mock data |
| `Overview.tsx` | ❌ Not checked | Likely mock data |

**No components import or use**:
- `import { api } from '../services/api'`
- `import { useQA, usePredict } from '../hooks/useAPI'`

---

## 🔧 What's Needed to Complete Integration

### 1. Backend Data Setup (Critical)
Run the data ingestion pipeline:
```bash
cd IDP
python step1_ingest_postgres.py  # Requires clean_cases_final_balanced.jsonl
python step3_build_pageindex.py
python step4_build_bm25.py
```

### 2. Update Frontend Components
Replace mock data with real API calls. Example for `AIQA.tsx`:

**Before** (current):
```typescript
const handleSend = () => {
  // Simulate AI response
  setTimeout(() => {
    const aiMsg = { /* mock data */ };
    setMessages(prev => [...prev, aiMsg]);
  }, 1000);
};
```

**After** (with API):
```typescript
import { useQA } from '../hooks/useAPI';

const { askQuestion, loading, error } = useQA();

const handleSend = async () => {
  try {
    const response = await askQuestion({ question: input, top_k: 3 });
    const aiMsg = {
      id: Date.now().toString(),
      role: 'assistant',
      content: response.answer,
      citations: response.sources,
      confidence: response.confidence
    };
    setMessages(prev => [...prev, aiMsg]);
  } catch (err) {
    console.error('API Error:', err);
  }
};
```

### 3. Build Frontend
```bash
cd frontend
npm run build
```

---

## 📊 Endpoint Test Results

### ✅ Working Endpoints
- `GET /` - API root (returns endpoint list)
- `GET /docs` - FastAPI Swagger docs

### ❌ Failing Endpoints (Data Missing)
- `POST /api/qa` - Internal Server Error (no BM25 index)
- `POST /api/predict` - Validation error (section format)
- `POST /api/draft` - Internal Server Error (no BM25 index)
- `GET /api/analytics/*` - Internal Server Error (no database data)
- `GET /health` - Returns "unhealthy" status

### 🧪 Test Commands
```bash
# Test root endpoint
curl http://localhost:8002/

# Test health check
curl http://localhost:8002/health

# Test Q&A (will fail without data)
curl -X POST http://localhost:8002/api/qa \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Section 8(1)(j)?", "top_k": 3}'

# Test analytics (will fail without data)
curl http://localhost:8002/api/analytics/denial-rates
```

---

## 📝 Summary

### What Works
1. ✅ Backend server running on port 8002
2. ✅ API service layer created (`api.ts`, `useAPI.ts`)
3. ✅ Vite proxy configured
4. ✅ CORS configured for frontend
5. ✅ All endpoint routes defined

### What Doesn't Work
1. ❌ Backend endpoints fail (no data files)
2. ❌ Frontend components use mock data (not integrated)
3. ❌ Database empty (no cases)
4. ❌ BM25 index missing
5. ❌ ML model missing

### Next Steps
1. **Run data ingestion pipeline** to populate database and build indices
2. **Update frontend components** to use API service layer
3. **Test end-to-end** integration
4. **Build frontend** for production

---

## 🔗 Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React)                         │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Components (AIQA, Predictor, Analytics, etc.)        │ │
│  │  - Currently use mock data                             │ │
│  │  - Need to import useAPI hooks                         │ │
│  └────────────────────────────────────────────────────────┘ │
│                           ↓                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Hooks (useQA, usePredict, useAnalytics)              │ │
│  │  ✅ Created - ready to use                             │ │
│  └────────────────────────────────────────────────────────┘ │
│                           ↓                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  API Service (api.ts)                                  │ │
│  │  ✅ Created - handles all HTTP requests                │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            ↓
                    Vite Proxy (/api → :8002)
                    ✅ Configured
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  Backend (FastAPI) :8002                     │
│  ✅ Running                                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Routers (qa, predict, draft, analytics)              │ │
│  │  ✅ All routes defined                                  │ │
│  └────────────────────────────────────────────────────────┘ │
│                           ↓                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Data Layer                                            │ │
│  │  ❌ Database empty                                      │ │
│  │  ❌ BM25 index missing                                  │ │
│  │  ❌ ML model missing                                    │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

**Generated**: 2026-05-09  
**Backend**: http://localhost:8002  
**Frontend**: http://localhost:5173 (when dev server runs)  
**API Docs**: http://localhost:8002/docs
