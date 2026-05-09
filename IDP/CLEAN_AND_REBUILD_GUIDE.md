# 🔄 Complete Clean and Rebuild Guide

## Overview

This guide walks you through completely cleaning all databases and rebuilding from scratch using your JSONL file.

---

## 🗑️ What Gets Cleaned

### PostgreSQL Database
- ✅ `cases` table (all cases)
- ✅ `paragraphs` table (all paragraphs)
- ✅ `ministries` table (all ministries)
- ✅ `ministry_stats` table
- ✅ `section_stats` table
- ✅ `workflow_sessions` table
- ✅ `workflow_actions` table

**Schema is kept intact** - only data is deleted.

### MongoDB Collections
- ✅ `rti_lens.documents` (all documents)
- ✅ `rti_lens.chunks` (all chunks)
- ✅ `rti_lens.document_trees` (all trees)
- ✅ `rtilens_vectors.document_embeddings` (all embeddings)

**Collections are kept** - only documents are deleted.

### Files
- ✅ All markdown files in `data/cic_orders_md/`
- ✅ All PageIndex trees in `data/pageindex_trees/`
- ✅ BM25 index file `data/bm25_pageindex.pkl`

**Directories are kept** - only files are deleted.

---

## 🚀 Quick Start (Recommended)

### Option 1: Automated Clean & Rebuild

**Run this single command:**

```cmd
cd "C:\Users\WIN11\Downloads\IDP 2\IDP"
clean_and_rebuild.bat
```

This will:
1. Clean all databases and files
2. Ask for confirmation
3. Rebuild everything from JSONL
4. Show progress for each step

**Total time: 30-60 minutes**

---

## 📋 Step-by-Step Process

### Option 2: Manual Steps

If you prefer to run steps separately:

#### Step 1: Clean Everything

```cmd
cd "C:\Users\WIN11\Downloads\IDP 2\IDP"
python cleanup_all_databases.py
```

**What happens:**
- Deletes all PostgreSQL data
- Deletes all MongoDB documents
- Deletes all files
- Asks for confirmation before proceeding

**Time: 1-2 minutes**

#### Step 2: Rebuild Everything

```cmd
cd "C:\Users\WIN11\Downloads\IDP 2\IDP"
python rebuild_from_jsonl.py
```

**What happens:**
- Processes 900 cases from JSONL
- Populates PostgreSQL
- Creates markdown files
- Populates MongoDB
- Builds PageIndex trees
- Builds BM25 index
- Builds vector embeddings

**Time: 30-60 minutes**

---

## ✅ Verification

After completion, verify everything is rebuilt:

```cmd
cd "C:\Users\WIN11\Downloads\IDP 2\IDP"
python -c "from pathlib import Path; from pymongo import MongoClient; from sqlalchemy import create_engine, text; import os; print('=== VERIFICATION ==='); engine = create_engine('postgresql://mohitsahoo@localhost:5432/rtilens'); conn = engine.connect(); print(f'PostgreSQL cases: {conn.execute(text(\"SELECT COUNT(*) FROM cases\")).scalar()}'); print(f'PostgreSQL paragraphs: {conn.execute(text(\"SELECT COUNT(*) FROM paragraphs\")).scalar()}'); print(f'PostgreSQL ministries: {conn.execute(text(\"SELECT COUNT(*) FROM ministries\")).scalar()}'); conn.close(); client = MongoClient('mongodb://localhost:27017/'); print(f'MongoDB documents: {client[\"rti_lens\"][\"documents\"].count_documents({})}'); print(f'MongoDB embeddings: {client[\"rtilens_vectors\"][\"document_embeddings\"].count_documents({})}'); client.close(); print(f'Markdown files: {len(list(Path(\"data/cic_orders_md\").glob(\"*.md\")))}'); print(f'PageIndex trees: {len(list(Path(\"data/pageindex_trees\").glob(\"*.json\")))}'); print(f'BM25 index: {Path(\"data/bm25_pageindex.pkl\").exists()}')"
```

**Expected output:**
```
=== VERIFICATION ===
PostgreSQL cases: 900
PostgreSQL paragraphs: ~10000+
PostgreSQL ministries: ~50+
MongoDB documents: 900
MongoDB embeddings: ~10000+
Markdown files: 900
PageIndex trees: 900
BM25 index: True
```

---

## 🎯 What You'll Have After Rebuild

### Databases
✅ **PostgreSQL** - Fully populated
- 900 cases with metadata
- ~10,000+ paragraphs
- ~50+ ministries
- Statistics tables ready

✅ **MongoDB** - Fully populated
- 900 documents in `rti_lens`
- ~10,000+ vector embeddings in `rtilens_vectors`
- Ready for semantic search

### Files
✅ **Markdown files** - 900 files
- One per case
- With metadata headers
- Ready for PageIndex processing

✅ **PageIndex trees** - 900 JSON files
- Hierarchical document structure
- Used for intelligent chunking

✅ **BM25 index** - Single file (~29 MB)
- Keyword search index
- Built from all paragraphs

### Search Capabilities
✅ **Keyword search** (BM25)
✅ **Semantic search** (Vector embeddings)
✅ **Hybrid search** (Combined)
✅ **Timeline visualization**
✅ **Q&A system**
✅ **Query optimization**

---

## 🐛 Troubleshooting

### Issue: "PostgreSQL connection failed"
**Solution:** Ensure PostgreSQL is running
```cmd
pg_ctl status
```

### Issue: "MongoDB connection failed"
**Solution:** Ensure MongoDB is running
```cmd
net start MongoDB
```

### Issue: "Permission denied"
**Solution:** Run Command Prompt as Administrator

### Issue: "JSONL file not found"
**Solution:** Verify file exists
```cmd
dir "C:\Users\WIN11\Downloads\IDP 2\IDP\clean_cases_final_balanced.jsonl"
```

### Issue: "Out of memory during embeddings"
**Solution:** This is normal for large datasets. The script will continue.

---

## ⚠️ Important Notes

1. **Backup First**: If you have any custom data, back it up before cleaning
2. **Time Required**: Set aside 30-60 minutes for the full process
3. **Don't Interrupt**: Let each step complete fully
4. **Check Logs**: Monitor the terminal for any errors
5. **Verify After**: Always verify the rebuild was successful

---

## 🎬 Ready to Start?

**Run this command now:**

```cmd
cd "C:\Users\WIN11\Downloads\IDP 2\IDP"
clean_and_rebuild.bat
```

Or run steps separately:

```cmd
# Step 1: Clean
python cleanup_all_databases.py

# Step 2: Rebuild
python rebuild_from_jsonl.py
```

---

## 📊 Progress Tracking

The scripts will show:
- ✅ Green checkmarks for completed steps
- ⚠️ Yellow warnings for non-critical issues
- ❌ Red X for failures
- Progress bars for long operations
- Counts and statistics at each step

---

## 🎉 After Completion

Once rebuild is complete:

### 1. Start Backend
```cmd
uvicorn backend.main:app --host 0.0.0.0 --port 8001 --reload
```

### 2. Start Frontend
```cmd
streamlit run streamlit_app.py
```

### 3. Test System
- Open http://localhost:8501
- Try Q&A with a question
- Check Timeline tab
- Verify search results

---

**Ready? Let's clean and rebuild!** 🚀
