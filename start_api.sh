#!/bin/bash
# RTI-Lens API Server Startup Script

echo "🚀 Starting RTI-Lens API Server..."
echo ""

# Check if PostgreSQL is running
if ! pg_isready -q; then
    echo "⚠️  PostgreSQL is not running. Starting it..."
    brew services start postgresql@14
    sleep 2
fi

# Check database connection
if psql -d rtilens -c "SELECT 1" > /dev/null 2>&1; then
    echo "✅ Database connection verified"
else
    echo "❌ Database connection failed"
    exit 1
fi

# Check if required files exist
if [ ! -f "data/bm25_pageindex.pkl" ]; then
    echo "❌ BM25 index not found. Run: python3 scripts/build_bm25.py"
    exit 1
fi

if [ ! -f "data/model.pkl" ]; then
    echo "❌ ML model not found. Run: python3 scripts/train_classifier.py"
    exit 1
fi

echo "✅ All required files present"
echo ""
echo "Starting FastAPI server on http://localhost:8000"
echo "API Documentation: http://localhost:8000/docs"
echo ""

cd "$(dirname "$0")"
python3 backend/main.py
