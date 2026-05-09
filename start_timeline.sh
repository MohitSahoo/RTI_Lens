#!/bin/bash
# Quick Start Script for Timeline Visualization
# Run this script to set up and launch RTI-Lens with Timeline Visualization

set -e  # Exit on error

echo "🚀 RTI-Lens Timeline Visualization - Quick Start"
echo "=================================================="
echo ""

# Check if we're in the right directory
if [ ! -f "streamlit_app.py" ]; then
    echo "❌ Error: Please run this script from the IDP directory"
    exit 1
fi

# Step 1: Install dependencies
echo "📦 Step 1: Installing dependencies..."
if command -v pip &> /dev/null; then
    pip install plotly==5.18.0
    echo "✅ Plotly installed"
else
    echo "❌ Error: pip not found. Please install Python and pip first."
    exit 1
fi

# Step 2: Check if backend is running
echo ""
echo "🔍 Step 2: Checking if backend is running..."
if curl -s http://localhost:8001/health > /dev/null 2>&1; then
    echo "✅ Backend is running on port 8001"
else
    echo "⚠️  Backend is not running. Starting it now..."
    echo "   Run this in a separate terminal:"
    echo "   uvicorn backend.main:app --host 0.0.0.0 --port 8001 --reload"
    echo ""
    read -p "Press Enter once backend is running..."
fi

# Step 3: Launch Streamlit
echo ""
echo "🎨 Step 3: Launching Streamlit frontend..."
echo ""
echo "✅ Setup complete! Opening Streamlit..."
echo ""
echo "📝 Quick Guide:"
echo "   1. Navigate to the '📅 Timeline' tab"
echo "   2. Select 'Demo: Sample Timeline' to see it in action"
echo "   3. Try 'Case Timeline' to visualize real data"
echo ""
echo "🌐 Opening browser at http://localhost:8501"
echo ""

streamlit run streamlit_app.py
