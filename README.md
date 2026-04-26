# RTI-Lens: AI-Powered CIC Order Analytics

AI platform for analyzing India's RTI Act rulings from the Central Information Commission. Predicts appeal success, analyzes denial patterns, queries 700+ rulings, and drafts appeals with precedent citations.

**Stack**: FastAPI + PostgreSQL + Gemini Flash RAG
**Docs**: [RTI_Lens_PRD.md](RTI_Lens_PRD.md)

## Quick Start

**Prerequisites:**
- PostgreSQL 14+ running
- Python 3.12+
- NLTK stopwords data

**Setup:**
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Download NLTK data
python3 -c "import nltk; nltk.download('stopwords')"

# 3. Start PostgreSQL (macOS)
brew services start postgresql@14

# 4. Create database and load schema
psql -U mohitsahoo -d postgres -c "CREATE DATABASE rtilens"
psql -U mohitsahoo -d rtilens -f schema.sql

# 5. Configure environment
cp .env.example .env
# Edit .env with your API keys (GEMINI_API_KEY required)

# 6. Add your CIC order data
# Place TXT files in data/cic_orders_txt/
# See data/README.md for format details

# 7. Build data files (BM25 index, PageIndex trees, etc.)
./setup_data.sh

# 8. Start API
./start_api.sh
```

**Test:**
```bash
./check_system.sh        # System health check
./test_all_endpoints.sh  # Full API test suite
```

**Access:**
- API: http://localhost:8001
- Docs: http://localhost:8001/docs
- GraphQL: http://localhost:8001/graphql

**Frontend (Streamlit):**
```bash
# Start frontend (API must be running first)
./start_frontend.sh
```
- Frontend: http://localhost:8501
- Features: Q&A, Appeal Drafting, Outcome Prediction, Analytics, Knowledge Graph

## Deployment

**Streamlit Cloud:**
1. Fork/push repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Deploy `streamlit_app.py`
4. Add secret in dashboard: `API_BASE_URL = "https://your-backend-url.com"`
5. App auto-deploys on push

**Backend (Render/Railway/Fly.io):**
- Deploy FastAPI backend first
- Set environment variables from `.env.example`
- Ensure PostgreSQL database accessible
- Note backend URL for Streamlit config

## Secrets

- Use `.env.example` as the only committed template.
- Keep real credentials only in `.env`, which is gitignored.
- `GEMINI_API_KEY` is required for the Q&A and draft flows.
- `OPENAI_API_KEY` is optional unless you are working on code paths that explicitly require it.
- If a key is exposed, revoke and rotate it immediately.

Detailed guidance: [SECURITY.md](SECURITY.md)

---

## 📋 Work Distribution

### Backend Team (Mohit & Saksham)

**Phase A: Database & ORM** ✅ COMPLETE
- [x] Migrate raw SQL to SQLAlchemy ORM
- [x] Define ORM schema for CIC orders
- [x] Implement typed database queries
- [x] Test data integrity after migration

**Phase B: API Layer** ✅ COMPLETE
- [x] Design GraphQL schema
- [x] Implement GraphQL resolvers (6 queries, 1 mutation)
- [x] Build enhanced knowledge graph with NetworkX
- [x] Integrate GraphQL with FastAPI at /graphql

**Phase C: DevOps**
- [ ] Create Dockerfile for backend
- [ ] Setup GitHub Actions CI/CD
- [ ] Configure automated testing pipeline
- [ ] Deploy to production environment

**Phase D: Frontend Integration**
- [ ] Build React dashboard UI
- [ ] Implement Q&A interface
- [ ] Create appeal drafting interface
- [ ] Connect frontend to GraphQL API

---

### Simulation & Blockchain Team (Aditya)

**Government Simulation**
- [ ] Design government entity models
- [ ] Implement ministry behavior simulation
- [ ] Create decision-making algorithms
- [ ] Build simulation dashboard

**Blockchain Integration**
- [ ] Design blockchain architecture for RTI tracking
- [ ] Implement smart contracts for transparency
- [ ] Build blockchain explorer interface
- [ ] Integrate with main platform

**Testing & Validation**
- [ ] Test simulation accuracy
- [ ] Validate blockchain transactions
- [ ] Performance benchmarking
- [ ] Documentation

