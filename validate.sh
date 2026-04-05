#!/bin/bash
# Quick validation script for RTI-Lens project

echo "🔍 RTI-Lens Project Validation"
echo "================================"
echo ""

# Check database
echo "1. Checking database..."
if psql -d rtilens -c "SELECT COUNT(*) FROM cases;" > /dev/null 2>&1; then
    CASES=$(psql -d rtilens -t -c "SELECT COUNT(*) FROM cases;")
    PARAGRAPHS=$(psql -d rtilens -t -c "SELECT COUNT(*) FROM paragraphs;")
    echo "   ✅ Database: $CASES cases, $PARAGRAPHS paragraphs"
else
    echo "   ❌ Database connection failed"
    exit 1
fi

# Check data files
echo ""
echo "2. Checking data files..."
if [ -f "data/bm25_pageindex.pkl" ]; then
    SIZE=$(ls -lh data/bm25_pageindex.pkl | awk '{print $5}')
    echo "   ✅ BM25 index: $SIZE"
else
    echo "   ❌ BM25 index missing"
fi

if [ -f "data/model.pkl" ]; then
    SIZE=$(ls -lh data/model.pkl | awk '{print $5}')
    echo "   ✅ ML model: $SIZE"
else
    echo "   ❌ ML model missing"
fi

if [ -f "data/cases.csv" ]; then
    SIZE=$(ls -lh data/cases.csv | awk '{print $5}')
    echo "   ✅ Cases CSV: $SIZE"
else
    echo "   ❌ Cases CSV missing"
fi

# Check backend files
echo ""
echo "3. Checking backend structure..."
BACKEND_FILES=$(find backend -name "*.py" | wc -l)
echo "   ✅ Backend files: $BACKEND_FILES Python files"

# Check scripts
echo ""
echo "4. Checking scripts..."
SCRIPTS=$(ls scripts/*.py 2>/dev/null | wc -l)
echo "   ✅ Scripts: $SCRIPTS Python scripts"

# Test imports
echo ""
echo "5. Testing Python imports..."
if python3 -c "from backend.main import app" 2>/dev/null; then
    echo "   ✅ FastAPI app imports successfully"
else
    echo "   ❌ FastAPI import failed"
fi

if python3 -c "from backend.utils.bm25_loader import BM25Loader; BM25Loader()" 2>/dev/null; then
    echo "   ✅ BM25 loader works"
else
    echo "   ❌ BM25 loader failed"
fi

# Summary
echo ""
echo "================================"
echo "✅ Validation Complete!"
echo "================================"
echo ""
echo "To start the API server:"
echo "  python3 backend/main.py"
echo ""
echo "To test the API:"
echo "  python3 test_api.py"
