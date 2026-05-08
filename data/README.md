# Data Directory Structure

This directory contains CIC order data and generated artifacts.

## Directory Layout

```
data/
├── cic_orders_txt/          # Raw CIC order text files (place your files here)
│   ├── EXAMPLE_CIC_ORDER.txt  # Example format reference
│   └── *.txt                  # Your CIC order files
├── cic_orders_md/           # Generated: Markdown conversions (auto-created)
├── pageindex_trees/         # Generated: PageIndex JSON trees (auto-created)
├── bm25_pageindex.pkl       # Generated: BM25 search index (~29MB)
├── model.pkl                # Generated: ML model (~3.5MB)
├── model_card.json          # Generated: Model metadata
├── dashboard_graph.json     # Generated: Knowledge graph
└── order_number_mapping.json # Generated: Order number mappings
```

## Setup Instructions

### 1. Add Your Data

Place CIC order TXT files in `data/cic_orders_txt/`:
- See `EXAMPLE_CIC_ORDER.txt` for format reference
- Files should be plain text CIC orders
- Filename format: `<hash>.txt` or any `.txt` name

### 2. Run Setup Script

From project root:
```bash

./setup_data.sh
```

This will:
1. Ingest TXT files into PostgreSQL database
2. Build BM25 search index
3. Generate PageIndex trees
4. Build dashboard knowledge graph

### 3. Verify

Check generated files:
```bash
ls -lh data/*.pkl data/*.json
ls data/pageindex_trees/ | wc -l  # Should match ingested cases
```

## File Descriptions

### Input Files
- **cic_orders_txt/*.txt**: Raw CIC order text files from web scraping

### Generated Files (Not in Git)
- **bm25_pageindex.pkl**: BM25 index for fast text retrieval
- **model.pkl**: RandomForest ML model for outcome prediction
- **model_card.json**: Model performance metrics
- **cic_orders_md/**: Markdown conversions of orders
- **pageindex_trees/**: Hierarchical document trees for RAG
- **dashboard_graph.json**: Ministry-section relationship graph
- **order_number_mapping.json**: Hash to order number mapping

## Data Sources

CIC orders scraped from: https://cic.gov.in/

## Notes

- Generated files are gitignored (too large for repo)
- Each user builds locally from their TXT files
- Example file provided for format reference
- Minimum ~100 TXT files recommended for meaningful results
