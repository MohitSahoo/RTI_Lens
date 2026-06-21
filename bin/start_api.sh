#!/bin/bash
# RTI-Lens API Startup Script

set -e

echo "🚀 Starting RTI-Lens API..."
echo ""

# Check PostgreSQL
if ! pg_isready -U mohitsahoo > /dev/null 2>&1; then
    echo "❌ PostgreSQL not running. Starting..."
    brew services start postgresql@14
    sleep 2
fi

# Check database exists
if ! psql -U mohitsahoo -lqt | cut -d \| -f 1 | grep -qw rtilens; then
    echo "❌ Database 'rtilens' not found. Creating..."
    psql -U mohitsahoo -d postgres -c "CREATE DATABASE rtilens"
    psql -U mohitsahoo -d rtilens -f migrations/sql/schema.sql
fi

# Check .env
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    exit 1
fi

# Check required data files
if [ ! -f data/bm25_pageindex.pkl ]; then
    echo "❌ BM25 index not found at data/bm25_pageindex.pkl"
    exit 1
fi

if [ ! -f data/model.pkl ]; then
    echo "❌ ML model not found at data/model.pkl"
    exit 1
fi

# Kill existing process on port 8001
if lsof -ti:8001 > /dev/null 2>&1; then
    echo "⚠️  Port 8001 in use. Stopping existing process..."
    # Try graceful shutdown first
    lsof -ti:8001 | xargs kill 2>/dev/null || true
    sleep 2
    # Force kill if still running
    if lsof -ti:8001 > /dev/null 2>&1; then
        lsof -ti:8001 | xargs kill -9 2>/dev/null || true
        sleep 1
    fi
fi

# Set PYTHONPATH and start API
export PYTHONPATH=$(pwd)
echo "✅ Starting API on http://localhost:8001"
echo "📚 Docs available at http://localhost:8001/docs"
echo ""

python3 backend/main.py
