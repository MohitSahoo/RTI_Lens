# RTI-Lens — Developer & Agent Workflow Guide

📚 **TECHNICAL DOCUMENTATION**
- **Type**: Operational Workflow & Agent Protocol
- **Audience**: Developers, AI Coding Agents
- **Status**: Stable v1.0

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🚁 1. The "Source of Truth" Map

When working on this project (especially as an AI agent), consult these files in the following order to maintain context:

| Priority | File | Purpose | Why read it? |
|:---|:---|:---|:---|
| 1 | **[README.md](file:///Users/mohitsahoo/Desktop/IDP/README.md)** | Project Status & Pulse | Understand what is built vs. what is v2.0. |
| 2 | **[RTI_Lens_PRD.md](file:///Users/mohitsahoo/Desktop/IDP/RTI_Lens_PRD.md)** | Product Goals | Verify if a feature aligns with Goals G1–G5. |
| 3 | **[docs/implementation_plan.md](file:///Users/mohitsahoo/Desktop/IDP/docs/implementation_plan.md)** | Technical Blueprint | Reference the chosen stack (Prisma, GraphQL, etc.). |
| 4 | **[docs/task.md](file:///Users/mohitsahoo/Desktop/IDP/docs/task.md)** | Execution Checklist | Find the next pending task (`[ ]`) to work on. |

---

## 🤖 2. Agent Handover Protocol

If you are an AI agent taking over this project, follow this prompt sequence:

> **Agent Prompt Suggestion:**
> "I am working on the RTI-Lens project. Please read `docs/task.md` to identify the current focus. Then, cross-reference the task with `docs/implementation_plan.md` for technical constraints and `RTI_Lens_PRD.md` for product requirements. Once you understand the context, suggest the implementation for the next pending task."

---

## 🛠️ 3. Development Workflow

### Step 1: Pre-requisites & Setup
Ensure the environment is ready before any feature implementation.
```bash
# 1. Start Postgres (Docker or Local)
brew services start postgresql@14

# 2. Sync dependencies
pip install -r requirements.txt

# 3. Verify current state
./validate.sh
```

### Step 2: Implementation (Feature/Fix)
Follow the Phase order in `docs/task.md`. **Never skip phases.**
1. **Infrastructure first**: Ensure Prisma/DB migrations are done.
2. **Logic second**: Implement the Python logic in routers/utils.
3. **API third**: Expose via REST or GraphQL.

### Step 3: Validation & Testing
Every change must be validated against the PRD.
- **Backend**: Run `pytest tests/` (once Phase C is reached).
- **Manual**: Use `python3 test_api.py` for quick smoke tests.
- **SQL**: Use `prisma validate` to ensure schema integrity.

### Step 4: Documentation (CRITICAL)
After every task completion:
1. Mark the task as `[x]` in `docs/task.md`.
2. Update `README.md` if an endpoint or feature status has changed.
3. If an architectural decision was changed, update `docs/implementation_plan.md`.

---

## ⚡ 4. Command Quick Reference

| Action | Command |
|:---|:---|
| **Start Backend** | `python3 backend/main.py` |
| **Prisma Sync** | `prisma db pull && prisma generate` |
| **Run Tests** | `pytest tests/ -v` |
| **Lint Check** | `ruff check backend/` |
| **Format Code** | `ruff format backend/` |
| **DB Access** | `psql -d rtilens` |

---

## 🛑 5. Guardrails

- **No Raw SQL**: Do not write `sqlalchemy.text()` strings. Use the Prisma client.
- **No PII On-Chain**: When implementing Phase E, only store SHA-256 hashes on the blockchain.
- **Grounded AI**: All Q&A/Draft features MUST use the PageIndex hierarchical re-ranker to prevent hallucinations.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 **TIP FOR AI AGENTS**:
Always verify that any code you write handles **async** correctly, as the entire RTI-Lens server is built on FastAPI's asynchronous architecture.
