# 🔄 Complete Rebuild Guide

## Overview

This guide walks you through rebuilding the entire RTI-Lens system from your JSONL file (`clean_cases_final_balanced.jsonl`).

---

## 📋 What Gets Rebuilt

### 1. **Markdown Files** (`data/cic_orders_md/`)
- 900 markdown files created from JSONL
- One file per case with metadata header
- Named using MD5 hash of order number

### 2. **MongoDB Collections** (`rti_lens` database)
- `documents`: Full case documents
- `chunks`: Document chunks for retrieval
- `document_trees`: PageIndex tree structures

### 3. **PageIndex Trees** (`data/pageindex_trees/`)
- Hierarchical JSON structures
- One tree per document
- Used for intelligent chunking

### 4. **BM25 Index** (`data/bm25_pageindex.pkl`)
- Keyword-based search index
- ~29 MB file
- Built from paragraph data

### 5. **Vector Embeddings** (`rtilens_vectors` database)
- Semantic search embeddings
- ~10,000+ embedding chunks
- Model: all-MiniLM-L6-v2 (384 dimensions)

---

## 🚀 Quick Start

### Option 1: Automated Rebuild (Recommended)

**Windows Command Prompt:**
```cmd
cd "C:\Users\WIN11\Downloads\IDP 2\IDP"
python rebuild_from_jsonl.py
```

**Or use the batch file:**
```cmd
cd "C:\Users\WIN11\Downloads\IDP 2\IDP"
rebuild_from_jsonl.bat
```

The script will:
1. Ask for confirmation
2. Run all 4 steps automatically
3. Show progress for each step
4. Provide a summary at the end

---

## 📊 Step-by-Step Process

### Step 1: Process JSONL (5-10 minutes)
```
Processing 900 cases...
├── Creating markdown files
├── Storing in MongoDB
└── Building order mapping
```

**Output:**
- 900 markdown files in `data/cic_orders_md/`
- 900 documents in MongoDB `rti_lens.documents`
- `data/order_number_mapping.json` created

### Step 2: Build PageIndex Trees (10-20 minutes)
```
Building PageIndex trees...
├── Running PageIndex on each markdown
├── Extracting hierarchical structure
└── Saving JSON trees
```

**Output:**
- 900 JSON files in `data/pageindex_trees/`
- Each file contains document structure

### Step 3: Build BM25 Index (2-5 minutes)
```
Building BM25 index...
├── Loading paragraphs from database
├── Tokenizing text
└── Creating BM25 index
```

**Output:**
- `data/bm25_pageindex.pkl` (~29 MB)
- Index covers all paragraphs

### Step 4: Build Vector Embeddings (15-30 minutes)
```
Building embeddings...
├── Loading embedding model
├── Chunking documents with PageIndex
├── Generating embeddings
└── Storing in MongoDB
```

**Output:**
- ~10,000+ embeddings in `rtilens_vectors.document_embeddings`
- Ready for semantic search

---

## ⏱️ Estimated Time

| Step | Time | Can Skip? |
|------|------|-----------|
| Process JSONL | 5-10 min | ❌ No |
| PageIndex Trees | 10-20 min | ⚠️ Optional* |
| BM25 Index | 2-5 min | ❌ No |
| Vector Embeddings | 15-30 min | ⚠️ Optional* |

**Total: 30-60 minutes**

*Optional steps can be skipped if you only need basic search functionality.

---

## 🔍 Verify Rebuild

After completion, verify with:

```cmd
cd "C:\Users\WIN11\Downloads\IDP 2\IDP"
python -c "from pathlib import Path; from pymongo import MongoClient; import os; print('Markdown files:', len(list(Path('data/cic_orders_md').glob('*.md')))); print('PageIndex trees:', len(list(Path('data/pageindex_trees').glob('*.json')))); print('BM25 index:', Path('data/bm25_pageindex.pkl').exists()); client = MongoClient(os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')); print('MongoDB docs:', client['rti_lens']['documents'].count_documents({})); print('Embeddings:', client['rtilens_vectors']['document_embeddings'].count_documents({})); client.close()"
```

**Expected output:**
```
Markdown files: 900
PageIndex trees: 900
BM25 index: True
MongoDB docs: 900
Embeddings: 10000+
```

---

## 🐛 Troubleshooting

### Issue: "JSONL file not found"
**Solution:** Ensure file is in the IDP directory
```cmd
dir "C:\Users\WIN11\Downloads\IDP 2\IDP\clean_cases_final_balanced.jsonl"
```

### Issue: "MongoDB connection failed"
**Solution:** Start MongoDB
```cmd
net start MongoDB
```

Or check if it's running:
```cmd
mongo --eval "db.version()"
```

### Issue: "PageIndex build failed"
**Solution:** Check if pageindex_lib exists
```cmd
dir "C:\Users\WIN11\Downloads\IDP 2\IDP\pageindex_lib"
```

### Issue: "Out of memory"
**Solution:** Process in batches or increase system memory

### Issue: "Embeddings taking too long"
**Solution:** This is normal for 900 documents. Be patient or use GPU acceleration if available.

---

## 📝 Manual Rebuild (If Automated Fails)

If the automated script fails, run steps manually:

### Step 1: Process JSONL
```cmd
cd "C:\Users\WIN11\Downloads\IDP 2\IDP"
python -c "import rebuild_from_jsonl; orch = rebuild_from_jsonl.RebuildOrchestrator(); orch.step1_process_jsonl()"
```

### Step 2: Build PageIndex
```cmd
python scripts/build_pageindex.py
```

### Step 3: Build BM25
```cmd
python scripts/build_bm25.py
```

### Step 4: Build Embeddings
```cmd
python scripts/build_embeddings.py
```

---

## 🎯 After Rebuild

Once rebuild is complete:

### 1. Start the Backend
```cmd
cd "C:\Users\WIN11\Downloads\IDP 2\IDP"
uvicorn backend.main:app --host 0.0.0.0 --port 8001 --reload
```

### 2. Start the Frontend
```cmd
cd "C:\Users\WIN11\Downloads\IDP 2\IDP"
streamlit run streamlit_app.py
```

### 3. Test the System
- Open http://localhost:8501
- Try Q&A tab with a question
- Check Timeline tab with case data
- Verify search results are relevant

---

## 📊 Data Flow

```
clean_cases_final_balanced.jsonl (900 cases)
    ↓
[Step 1: Process JSONL]
    ↓
├── data/cic_orders_md/*.md (900 files)
├── MongoDB rti_lens.documents (900 docs)
└── data/order_number_mapping.json
    ↓
[Step 2: Build PageIndex]
    ↓
data/pageindex_trees/*.json (900 trees)
    ↓
[Step 3: Build BM25]
    ↓
data/bm25_pageindex.pkl (29 MB)
    ↓
[Step 4: Build Embeddings]
    ↓
MongoDB rtilens_vectors.document_embeddings (10K+ chunks)
    ↓
[System Ready]
```

---

## 💡 Pro Tips

1. **Run overnight**: The full rebuild takes 30-60 minutes
2. **Check logs**: Monitor progress in terminal
3. **Don't interrupt**: Let each step complete
4. **Verify after each step**: Ensure data is created
5. **Backup first**: Keep a copy of your JSONL file

---

## 🆘 Need Help?

If rebuild fails:
1. Check the error message
2. Look in the troubleshooting section
3. Try manual rebuild steps
4. Verify all dependencies are installed
5. Check MongoDB is running

---

**Ready to rebuild? Run:**
```cmd
cd "C:\Users\WIN11\Downloads\IDP 2\IDP"
python rebuild_from_jsonl.py
```

The script will guide you through the process! 🚀
