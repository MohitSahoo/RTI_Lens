#!/bin/bash
set -e

echo "🔧 RTI Lens Data Setup"
echo "======================"
echo ""
echo "This script will build all required data files from your CIC order TXT files."
echo ""

# Check if data directory exists
if [ ! -d "data/cic_orders_txt" ]; then
    echo "❌ Error: data/cic_orders_txt/ directory not found"
    exit 1
fi

# Count TXT files
TXT_COUNT=$(find data/cic_orders_txt -name "*.txt" ! -name "EXAMPLE_*.txt" | wc -l | tr -d ' ')

if [ "$TXT_COUNT" -eq 0 ]; then
    echo "❌ Error: No CIC order TXT files found in data/cic_orders_txt/"
    echo ""
    echo "📝 Instructions:"
    echo "1. Place your CIC order TXT files in data/cic_orders_txt/"
    echo "2. See EXAMPLE_CIC_ORDER.txt for format reference"
    echo "3. Run this script again"
    exit 1
fi

echo "📊 Found $TXT_COUNT CIC order files"
echo ""

# Check database connection
echo "🔍 Checking database connection..."
if ! psql -U mohitsahoo -d rtilens -c "SELECT 1" > /dev/null 2>&1; then
    echo "❌ Error: Cannot connect to PostgreSQL database 'rtilens'"
    echo ""
    echo "📝 Setup database first:"
    echo "  psql -U mohitsahoo -d postgres -c \"CREATE DATABASE rtilens\""
    echo "  psql -U mohitsahoo -d rtilens -f migrations/sql/schema.sql"
    exit 1
fi
echo "✅ Database connected"
echo ""

# Confirm before proceeding
echo "⚠️  This will:"
echo "  1. Ingest $TXT_COUNT files into database"
echo "  2. Build BM25 index (~29MB)"
echo "  3. Build PageIndex trees"
echo "  4. Build dashboard graph"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

echo ""
echo "🚀 Starting data pipeline..."
echo ""

# Step 1: Ingest
echo "📥 Step 1/4: Ingesting CIC orders into database..."
PYTHONPATH=$(pwd) python3 scripts/ingest.py
echo "✅ Ingestion complete"
echo ""

# Step 2: Build BM25
echo "🔍 Step 2/4: Building BM25 index..."
PYTHONPATH=$(pwd) python3 scripts/build_bm25.py
echo "✅ BM25 index built"
echo ""

# Step 3: Build dashboard graph
echo "📊 Step 3/4: Building dashboard graph..."
PYTHONPATH=$(pwd) python3 scripts/build_dashboard_graph.py
echo "✅ Dashboard graph built"
echo ""

# Step 4: Verify
echo "🔍 Step 4/4: Verifying setup..."
PYTHONPATH=$(pwd) python3 scripts/validate_pageindex.py
echo "✅ Verification complete"
echo ""

echo "✅ Setup complete!"
echo ""
echo "📊 Generated files:"
echo "  - data/bm25_pageindex.pkl"
echo "  - data/model.pkl"
echo "  - data/pageindex_trees/*.json"
echo "  - data/dashboard_graph.json"
echo ""
echo "🚀 Start the API:"
echo "  ./start_api.sh"
