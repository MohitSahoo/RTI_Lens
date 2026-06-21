# RTI Lens — Product Requirements Document

**Version:** 1.0
**Status:** In Progress
**Last Updated:** May 24, 2026

---

## Table of Contents

1. [Product Overview](#product-overview)
2. [Goals & Success Metrics](#goals--success-metrics)
3. [System Architecture](#system-architecture)
4. [Module 1 — CICS Storage](#module-1--cics-storage)
5. [Module 2 — RAG Pipeline](#module-2--rag-pipeline)
6. [Module 3 — Query Assistant](#module-3--query-assistant)
7. [Module 4 — Multi-Agent Drafting System](#module-4--multi-agent-drafting-system)
8. [Module 5 — Accuracy Scoring & Orchestration](#module-5--accuracy-scoring--orchestration)
9. [Module 6 — State Management](#module-6--state-management)
10. [Non-Functional Requirements](#non-functional-requirements)
11. [Open Issues & Risks](#open-issues--risks)

---

## Product Overview

**RTI Lens** is an AI-powered Right to Information (RTI) query assistant that:

- Stores and indexes Central Information Commission (CIC) decisions (CICs)
- Retrieves relevant precedents using a hybrid RAG pipeline
- Drafts legally structured RTI queries using a multi-agent system
- Scores and merges the best drafts via an orchestrator model

**Primary Users:** Citizens, journalists, activists, and legal professionals filing RTI applications.

---

## Goals & Success Metrics

### Goals
- [ ] Provide a reliable, searchable CIC precedent database
- [ ] Generate high-quality, legally accurate RTI query drafts
- [ ] Automate ministry and section identification from user intent
- [ ] Score each draft for acceptance likelihood before presenting it

### Success Metrics
- [ ] RAG retrieval precision ≥ 85% on evaluation set (RAGAS)
- [ ] Draft acceptance score ≥ 50% on trained classifier
- [ ] End-to-end query generation latency < 15 seconds
- [ ] Structural verification pass rate ≥ 95%

---

## System Architecture

```
User Query
    │
    ▼
Query Assistant
    │
    ├── Ministry + Section Identifier
    │
    ▼
Hybrid RAG Pipeline
    ├── BM25 Search (PostgreSQL — paragraph-level)
    ├── Semantic Search (MongoDB Atlas Vector)
    └── Structural Verification (Page Index)
    │
    ▼
Multi-Agent Drafting (3x Groq Agents)
    │
    ▼
Acceptance Scorer (Fine-tuned Model)
    │
    ▼
Gemini Orchestrator (Merge Best Drafts)
    │
    ▼
Final RTI Query Draft
```

---

## Module 1 — CICS Storage

### Description
Central repository for all CIC (Central Information Commission) decisions used as precedents.

### Requirements

- [ ] Define schema for CIC documents (case ID, date, ministry, section, full text, outcome)
- [ ] Ingest pipeline to parse and store raw CIC PDFs/HTML into structured records
- [ ] Tag each CIC with relevant ministry and RTI sections
- [ ] Store paragraph-level chunks in PostgreSQL for BM25 indexing
- [ ] Store vector embeddings in MongoDB Atlas for semantic search
- [ ] Support incremental updates when new CIC decisions are published
- [ ] Deduplication logic to avoid redundant CIC entries
- [ ] Admin interface or script to manually add/remove CIC records

### Data Schema (PostgreSQL — BM25)

| Field | Type | Notes |
|---|---|---|
| `cic_id` | UUID | Primary key |
| `case_number` | VARCHAR | Official CIC case ref |
| `ministry` | VARCHAR | Relevant ministry |
| `section` | VARCHAR | RTI Act section cited |
| `paragraph_index` | INT | Chunk position in doc |
| `paragraph_text` | TEXT | Chunk content |
| `decision_date` | DATE | Date of CIC order |
| `outcome` | VARCHAR | Allowed / Denied / Partial |

### Data Schema (MongoDB Atlas — Semantic)

| Field | Type | Notes |
|---|---|---|
| `_id` | ObjectId | MongoDB ID |
| `cic_id` | String | FK to PostgreSQL |
| `embedding` | Array[Float] | Vector embedding |
| `metadata` | Object | ministry, section, date |

---

## Module 2 — RAG Pipeline

### Description
Hybrid retrieval system combining keyword and semantic search, validated by structural checks, and evaluated using RAGAS + DeepEval.

### 2.1 BM25 Search (PostgreSQL)

- [ ] Implement BM25 full-text search index on `paragraph_text` column
- [ ] Accept query string, return top-K ranked paragraph chunks
- [ ] Support filtering by ministry and/or RTI section
- [ ] Return `cic_id`, `paragraph_index`, relevance score per result
- [ ] Tune BM25 parameters (k1, b) based on evaluation results

### 2.2 Semantic Search (MongoDB Atlas)

- [ ] Set up MongoDB Atlas Vector Search index on embedding field
- [ ] Embed incoming query using the same model used during ingestion
- [ ] Perform ANN (Approximate Nearest Neighbor) search, return top-K results
- [ ] Support pre-filtering by ministry/section metadata before vector search
- [ ] Handle Atlas connection failures gracefully with fallback to BM25-only

### 2.3 Structural Verification (Page Index)

- [ ] After retrieval, verify each result is correctly mapped to its source page/section
- [ ] Reject or flag chunks where page index is inconsistent with expected document structure
- [ ] Log all structural verification failures for audit
- [ ] Define pass/fail threshold for structural check (e.g., discard chunks with index mismatch)

### 2.4 RAG Fusion / Reranking

- [ ] Merge BM25 and semantic search result sets
- [ ] Apply reciprocal rank fusion (RRF) or weighted scoring to produce unified ranked list
- [ ] Final top-K (e.g., top 5) chunks passed to the drafting agents

### 2.5 Evaluation (RAGAS + DeepEval)

- [ ] Set up RAGAS evaluation suite: faithfulness, answer relevancy, context precision, context recall
- [ ] Set up DeepEval test cases for hallucination and correctness
- [ ] Create a golden evaluation dataset from manually verified CIC queries
- [ ] Run evals on every major pipeline change
- [ ] Dashboard or report to track eval metrics over time
- [ ] Define regression thresholds — block deploys if metrics drop below baseline

---

## Module 3 — Query Assistant (User Input Layer)

### Description
The interface where users describe what information they need. The system maps the query to a ministry and applicable RTI Act sections.

### Requirements

- [ ] Accept free-text user query (natural language)
- [ ] Ministry Identification: classify query to the correct ministry (e.g., MoHFW, MoE, MHA)
- [ ] Section Identification: map query intent to relevant RTI Act sections (e.g., Section 4, 6, 8)
- [ ] Display identified ministry + section to the user for confirmation before proceeding
- [ ] Allow user to override ministry/section if auto-detection is wrong
- [ ] Handle ambiguous queries — prompt user for clarification if confidence < threshold
- [ ] Log all queries with ministry/section predictions and user overrides for retraining

### Ministry + Section Classifier

- [ ] Define the list of supported ministries (enumerated list)
- [ ] Define RTI Act section taxonomy
- [ ] Train or prompt-engineer classifier (LLM-based or fine-tuned)
- [ ] Confidence threshold for auto-selection vs. asking user
- [ ] Evaluation dataset for classifier accuracy

---

## Module 4 — Multi-Agent Drafting System

### Description
Three parallel Groq agents with distinct prompting strategies draft the RTI query. Each agent uses the retrieved precedents as context.

### Requirements

- [ ] Retrieve top-K RAG results (precedents) before invoking agents
- [ ] Pass retrieved context + user query + ministry/section to all 3 agents

### Agent Definitions

| Agent | Prompt Strategy | Focus |
|---|---|---|
| Agent 1 | Formal legal tone | Strict adherence to RTI Act language |
| Agent 2 | Precedent-heavy | Cite CIC cases directly in the draft |
| Agent 3 | Plain language + completeness | Comprehensive information request |

- [ ] Define and version-control system prompts for all 3 agents
- [ ] Each agent returns a structured draft (subject line + body + sections cited)
- [ ] Implement retry logic if an agent fails or returns malformed output
- [ ] Log all agent outputs with metadata (latency, token count, model version)
- [ ] Support easy swapping of agents or adding a 4th agent without pipeline breaks

---

## Module 5 — Accuracy Scoring & Orchestration

### Description
A fine-tuned classifier scores each draft for likelihood of acceptance. The Gemini orchestrator selects and merges the best-scoring drafts into a final output.

### 5.1 Acceptance Scorer (Fine-tuned Model)

- [ ] Define what "acceptance" means — RTI officer accepting the query without rejection
- [ ] Collect training data: (draft text, label: accepted/rejected) from real RTI filings
- [ ] Fine-tune or train model (specify architecture: BERT-based, LLM with classifier head, etc.)
- [ ] Model outputs a score between 0–100% (acceptance probability)
- [ ] Define threshold: drafts below X% are filtered out before orchestration
- [ ] Version-control trained model artifacts
- [ ] Periodic retraining schedule as new RTI outcome data is collected
- [ ] Evaluation metrics for scorer: AUC-ROC, precision/recall on held-out set

### 5.2 Gemini Orchestrator

- [ ] Receive accepted drafts (those above score threshold) from scorer
- [ ] Gemini prompt: given N drafts + their scores, synthesize the best final RTI query
- [ ] Merging strategy: extract strongest elements from each draft (subject line, legal citations, body sections)
- [ ] Final output must include: subject line, full body, RTI sections cited, supporting CIC precedents
- [ ] Fallback: if all drafts are below threshold, return best-scoring draft with a warning
- [ ] Log orchestrator input/output for each request

---

## Module 6 — State Management (Blackboard.io)

### Description
Blackboard.io is used to manage application state across the multi-step pipeline.

### Requirements

- [ ] Define state schema for a single RTI query session:
  - User query
  - Identified ministry + section
  - Retrieved precedents (RAG results)
  - Agent drafts (all 3)
  - Acceptance scores per draft
  - Final merged output
  - Session status (in-progress / completed / failed)
- [ ] Persist state between pipeline steps so any step can resume on failure
- [ ] TTL/expiry policy for session state (e.g., auto-clean after 24 hours)
- [ ] Real-time state updates visible to frontend (progress indicator per step)
- [ ] Error state handling — record which step failed and why
- [ ] Audit log: every state transition stored with timestamp

---

## Non-Functional Requirements

### Performance
- [ ] RAG retrieval (BM25 + semantic combined) < 3 seconds per query
- [ ] Each Groq agent draft < 5 seconds
- [ ] Acceptance scorer inference < 1 second per draft
- [ ] Gemini orchestration < 5 seconds
- [ ] Total end-to-end < 15 seconds (P95)

### Reliability
- [ ] System must degrade gracefully — if semantic search (MongoDB Atlas) is unavailable, fall back to BM25 only
- [ ] If 1 of 3 Groq agents fails, proceed with remaining 2
- [ ] Retry failed steps up to 3 times before marking session as failed

### Security
- [ ] No user PII stored beyond session TTL
- [ ] MongoDB Atlas connection via TLS only
- [ ] All API keys stored in environment variables / secrets manager (never hardcoded)
- [ ] Rate limiting on the query assistant endpoint

### Observability
- [ ] Structured logging for every pipeline step
- [ ] Tracing: request ID propagated through all modules
- [ ] Alerts on: scorer model latency spike, Atlas connection failure, RAG eval metric regression

---

## Open Issues & Risks

| # | Issue | Priority | Owner | Status |
|---|---|---|---|---|
| 1 | MongoDB Atlas mandatory — no local fallback for semantic search | High | Infra | 🔴 Open |
| 2 | Acceptance scorer training data volume — is it sufficient? | High | ML | 🔴 Open |
| 3 | Ministry classifier accuracy on edge-case / multi-ministry queries | Medium | ML | 🟡 In Review |
| 4 | Blackboard.io state schema not finalised | Medium | Backend | 🟡 In Review |
| 5 | RAGAS golden dataset needs to be built manually | Medium | QA | 🔴 Open |
| 6 | Groq agent prompt versions not yet locked | Low | AI | 🟡 In Review |
| 7 | Gemini orchestrator merge strategy not formally defined | High | AI | 🔴 Open |

---

## Appendix — Tech Stack Summary

| Component | Technology |
|---|---|
| CIC Storage (BM25) | PostgreSQL |
| CIC Storage (Semantic) | MongoDB Atlas Vector Search |
| State Management | Blackboard.io |
| Drafting Agents | Groq (x3, different prompts) |
| Acceptance Scorer | Fine-tuned classifier model |
| Orchestrator | Gemini |
| RAG Evaluation | RAGAS + DeepEval |
| Embedding Model | TBD — must match ingestion + query |

---

*This PRD is a living document. All checkboxes represent open implementation tasks. Check them off as each requirement is shipped and verified.*
