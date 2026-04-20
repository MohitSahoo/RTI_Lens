# 👁️ RTI-Lens: Intelligent CIC Order Analytics

**An AI-Powered Platform for the Central Information Commission (CIC)**

[![Status: v2.0 In Progress](https://img.shields.io/badge/Status-v2.0%20In%20Progress-yellow.svg)](#)
[![Backend: Production Ready](https://img.shields.io/badge/Backend-Production%20Ready-success.svg)](#)
[![AI Engine: Gemini RAG](https://img.shields.io/badge/AI-Google%20Gemini-orange.svg)](#)
[![CI/CD: GitHub Actions](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-blue.svg)](#)

---

## 📋 Quick Links

- 📘 **Primary Blueprint**: [RTI_Lens_PRD.md](RTI_Lens_PRD.md) (All Requirements, Tech Stack, Roadmap & Tasks)
- 🚀 **Main Entrypoint**: `backend/main.py`
- 📊 **Dataset**: `rtilens` PostgreSQL DB (469 cases)

---

## 🎯 What is RTI-Lens?

RTI-Lens is a comprehensive platform engineered for parsing, analyzing, and interrogating India's Right to Information (RTI) Act rulings adjudicated by the Central Information Commission (CIC). By uniting **traditional Machine Learning** with **Generative AI (Gemini Flash)**, it empowers citizens to:

- **Predict success probability** of an appeal.
- **Analyze ministry-specific denial patterns.**
- **Query 700+ rulings** with grounded AI answers.
- **Draft superior appeals** citing CIC precedents automatically.

---

## 🏁 Quick Start Guide

**1. Clone and Configure**
```bash
echo "GEMINI_API_KEY=YOUR_KEY" >> .env
echo "DATABASE_URL=postgresql://user@localhost:5432/rtilens" >> .env
```

**2. Provision Environment**
```bash
pip install -r requirements.txt
```

**3. Start Server Operations**
```bash
python3 backend/main.py
# API available at http://localhost:8001
# Swagger docs at http://localhost:8001/docs
```

**4. Run Diagnostic Check**
```bash
python3 test_api.py
```

---

## 🏗️ v2.0 Roadmap

The current focus is on infrastructure modernization (Phase A-C) followed by a React-based frontend (Phase D).

| Phase | Milestone | Focus |
|---|---|---|
| **A** | **Prisma Migration** | Replace raw SQL with typed ORM |
| **B** | **GraphQL Layer** | Flexible API for React |
| **C** | **Docker & CI/CD** | Automated pipeline & containerization |
| **D** | **Frontend (React)** | Dashboard, Q&A, and Draft UIs |

> For the granular task list and architecture diagrams, see **[RTI_Lens_PRD.md](RTI_Lens_PRD.md)**.
