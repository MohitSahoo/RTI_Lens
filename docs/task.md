# RTI-Lens v2 — Task Tracker

**Project**: RTI-Lens — AI-Powered CIC Order Analytics
**PRD Version**: 2.0
**Status**: 🟡 Backend v1.0 Complete → v2.0 In Progress

---

## Product Goals Alignment

| PRD Goal | Description | Backend Status | Frontend Status |
|----------|-------------|----------------|-----------------|
| **G1** | Expose denial patterns per ministry and Section 8 clause | ✅ Complete (analytics API) | ❌ Not started |
| **G2** | Grounded, cited answers from CIC precedents | ✅ Complete (BM25 + PageIndex + Gemini QA) | ❌ Not started |
| **G3** | Help citizens draft better RTI queries | ✅ Complete (Co-Drafting API) | ❌ Not started |
| **G4** | Predict appeal success probability | ✅ Complete (ML classifier, F1 = 0.81) | ❌ Not started |
| **G5** | Tamper-proof filing via blockchain | ❌ Not started | ❌ Not started |

| Artifact | Status | Location |
|----------|--------|----------|
| Product PRD | ✅ Validated | `RTI_Lens_PRD.md` |
| Implementation Plan | ✅ Created | `docs/implementation_plan.md` |
| Task Tracker | ✅ Created | `docs/task.md` |
| Workflow Guide | ✅ Created | `docs/workflow.md` |

---

## Phase 0: Data Pipeline & Backend v1.0 (COMPLETE)

All PRD Phases 1–4 are finished. The working product foundation is in place.

- [x] **Ingest 712 TXT orders** → `scripts/ingest.py` → 469 cases, 43,151 paragraphs
- [x] **Compute ministry/section stats** → `scripts/compute_stats.py`
- [x] **Build BM25 search index** → `scripts/build_bm25.py` → 26 MB singleton
- [x] **Build PageIndex trees** → `scripts/txt_to_markdown.py` + `scripts/build_pageindex.py`
- [x] **Build order number mapping** → `scripts/build_order_mapping.py`
- [x] **Train ML classifier** → `scripts/train_classifier.py` → 81.25% accuracy
- [x] **Build knowledge graph** → `scripts/build_knowledge_graph.py`
- [x] **Analytics endpoints** → `/api/analytics/denial-rates`, `section-heatmap`, `override-trend`, `ministry/{id}/orders`
- [x] **RAG Q&A endpoint** → `/api/qa` (BM25 + PageIndex + Gemini + faithfulness check)
- [x] **Co-Drafting endpoint** → `/api/draft` (BM25 + section stats + Gemini)
- [x] **Prediction endpoint** → `/api/predict` (RandomForest + model card)
- [x] **Knowledge graph endpoint** → `/api/graph`
- [x] **Rate limiting & session tracking** → slowapi + in-memory session counter

---

## Phase A: Prisma ORM Migration

**Goal**: Type-safe database layer. Fix SQL injection vulnerability.

| ID | Task | File(s) | Verify | Status |
|:---|:-----|:--------|:-------|:-------|
| A.1 | Create Prisma schema from `schema.sql` | `prisma/schema.prisma` [NEW] | `prisma validate` | `[ ]` |
| A.2 | Introspect live database | CLI: `prisma db pull` | Models match 6 tables | `[ ]` |
| A.3 | Generate typed Python client | CLI: `prisma generate` | `.prisma/client` exists | `[ ]` |
| A.4 | Create async Prisma singleton | `backend/prisma_client.py` [NEW] | Import succeeds | `[ ]` |
| A.5 | Wire into FastAPI lifespan | `backend/main.py` [MODIFY] | Server starts cleanly | `[ ]` |
| A.6 | Migrate analytics router (4 queries) | `backend/routers/analytics.py` [MODIFY] | `/api/analytics/*` returns same data | `[ ]` |
| A.7 | Migrate draft router (1 query) | `backend/routers/draft.py` [MODIFY] | `/api/draft` works | `[ ]` |
| A.8 | Migrate predict router (1 query) | `backend/routers/predict.py` [MODIFY] | `/api/predict` works | `[ ]` |
| A.9 | Remove SQLAlchemy layer | `backend/database.py` [DELETE] | No `sqlalchemy` imports remain | `[ ]` |
| A.10 | Regression test all REST endpoints | `python3 test_api.py` | All 7 endpoints pass | `[ ]` |

---

## Phase B: GraphQL API Layer

**Goal**: Flexible query interface for the React frontend. Single endpoint for composable queries.

| ID | Task | File(s) | Verify | Status |
|:---|:-----|:--------|:-------|:-------|
| B.1 | Create GraphQL package | `backend/graphql/__init__.py` [NEW] | — | `[ ]` |
| B.2 | Define Strawberry types | `backend/graphql/types.py` [NEW] | Types match Pydantic schemas | `[ ]` |
| B.3 | Implement Query resolvers | `backend/graphql/resolvers.py` [NEW] | Query `{ ministries { name } }` works | `[ ]` |
| B.4 | Implement Mutation resolvers | `backend/graphql/resolvers.py` [MODIFY] | `askQuestion` mutation returns answer | `[ ]` |
| B.5 | Create schema entrypoint | `backend/graphql/schema.py` [NEW] | `strawberry.Schema` validates | `[ ]` |
| B.6 | Mount GraphQL router | `backend/main.py` [MODIFY] | `http://localhost:8001/graphql` loads | `[ ]` |
| B.7 | Test GraphiQL playground | Browser | Run sample queries manually | `[ ]` |

---

## Phase C: CI/CD & Docker

**Goal**: Containerize the app. Validate every push with lint → test → build.

| ID | Task | File(s) | Verify | Status |
|:---|:-----|:--------|:-------|:-------|
| C.1 | Create multi-stage Dockerfile | `Dockerfile` [NEW] | `docker build .` succeeds | `[ ]` |
| C.2 | Update docker-compose with app service | `docker-compose.yml` [MODIFY] | `docker-compose up` starts app + DB | `[ ]` |
| C.3 | Create GitHub Actions CI workflow | `.github/workflows/ci.yml` [NEW] | Lint → Test → Build passes | `[ ]` |
| C.4 | Add new dependencies | `requirements.txt` [MODIFY] | `pip install -r requirements.txt` works | `[ ]` |
| C.5 | Update .gitignore | `.gitignore` [MODIFY] | `.prisma/`, `node_modules/` ignored | `[ ]` |
| C.6 | Create test fixtures | `tests/conftest.py` [NEW] | Prisma + httpx fixtures work | `[ ]` |
| C.7 | Write analytics tests | `tests/test_analytics.py` [NEW] | 4 test cases pass | `[ ]` |
| C.8 | Write GraphQL tests | `tests/test_graphql.py` [NEW] | 3 test cases pass | `[ ]` |

---

## Phase D: React Frontend (PRD Phase 6)

**Goal**: Build the 4-page React app. This is the primary remaining product work.

| ID | Task | Component(s) | Verify | Status |
|:---|:-----|:-------------|:-------|:-------|
| D.1 | Scaffold Vite + React + Tailwind | `frontend/` [NEW] | `npm run dev` shows blank app | `[ ]` |
| D.2 | Build sidebar navigation | `<Sidebar />` | 4 nav links work | `[ ]` |
| D.3 | Dashboard: Denial bar chart | `<DenialBarChart />` | Top-10 ministries render | `[ ]` |
| D.4 | Dashboard: Section heatmap | `<SectionHeatmap />` | Color-coded grid renders | `[ ]` |
| D.5 | Dashboard: Override trend line | `<OverrideTrendLine />` | 24-month trend renders | `[ ]` |
| D.6 | Dashboard: Filters | `<FilterBar />` | Ministry, year, section filters work | `[ ]` |
| D.7 | Dashboard: Orders drill-down | `<OrdersTable />` | Click ministry → table loads | `[ ]` |
| D.8 | Q&A: Query input + answer | `<QueryInput />`, `<AnswerPanel />` | Ask question → get answer | `[ ]` |
| D.9 | Q&A: Sources panel | `<SourcesPanel />` | Collapsible source cards | `[ ]` |
| D.10 | Q&A: Faithfulness + session counter | `<FaithfulnessBanner />`, `<SessionCounter />` | Warning shows, counter decrements | `[ ]` |
| D.11 | Co-Drafter: Before/After | `<BeforeAfter />` | Side-by-side comparison renders | `[ ]` |
| D.12 | Co-Drafter: Change notes + avoid phrases | `<ChangeNotes />`, `<AvoidList />` | Cards and pills render | `[ ]` |
| D.13 | Predictor: Form + probability meter | `<PredictorForm />`, `<ProbabilityMeter />` | Arc gauge renders with probability | `[ ]` |
| D.14 | Predictor: Model card | `<ModelCard />` | Collapsible with disclaimer | `[ ]` |

---

## Phase E: Blockchain Integration (PRD Phase 5)

**Goal**: Deploy RTIRegistry contract. Add filing/verification endpoints.

| ID | Task | File(s) | Verify | Status |
|:---|:-----|:--------|:-------|:-------|
| E.1 | Write Solidity contract | `contracts/RTIRegistry.sol` [NEW] | Hardhat tests pass | `[ ]` |
| E.2 | Deploy to Polygon Mumbai | Hardhat deploy script | Contract address logged | `[ ]` |
| E.3 | Create web3.py client | `blockchain/client.py` [NEW] | `fileRTI()` returns TX hash | `[ ]` |
| E.4 | Build filing endpoint | `backend/routers/blockchain.py` [NEW] | `POST /api/blockchain/file` works | `[ ]` |
| E.5 | Build status endpoint | `backend/routers/blockchain.py` [MODIFY] | `GET /api/blockchain/status/{tx}` works | `[ ]` |
| E.6 | Frontend: File & Verify page | `<FilingForm />`, `<HashPreview />`, `<ConfirmationCard />` | End-to-end filing works | `[ ]` |

---

## Progress Summary

| Phase | Description | Tasks | Est. Time | Status |
|:------|:-----------|:------|:----------|:-------|
| **Phase 0** | Data Pipeline & Backend v1.0 | 13 | — | ✅ 100% |
| **Phase A** | Prisma ORM Migration | 10 | ~3 hrs | ⚪ 0% |
| **Phase B** | GraphQL API Layer | 7 | ~2.5 hrs | ⚪ 0% |
| **Phase C** | CI/CD & Docker | 8 | ~2 hrs | ⚪ 0% |
| **Phase D** | React Frontend | 14 | ~15 hrs | ⚪ 0% |
| **Phase E** | Blockchain Integration | 6 | ~8 hrs | ⚪ 0% |
| **Total** | | **58** | **~30.5 hrs** | 🟡 22% (Phase 0) |

---

## File Change Summary

| Action | Count | Key Files |
|--------|-------|-----------|
| **NEW** | ~20+ | `prisma/schema.prisma`, `backend/prisma_client.py`, `backend/graphql/*`, `Dockerfile`, `.github/workflows/ci.yml`, `tests/*`, `frontend/*`, `contracts/*`, `blockchain/client.py` |
| **MODIFY** | 7 | `backend/main.py`, `backend/routers/analytics.py`, `draft.py`, `predict.py`, `requirements.txt`, `docker-compose.yml`, `.gitignore` |
| **DELETE** | 1 | `backend/database.py` |
