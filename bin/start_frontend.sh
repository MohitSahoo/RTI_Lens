#!/bin/bash
# Launch Streamlit frontend for RTI-Lens

echo "Starting RTI-Lens Streamlit Frontend..."
echo "Make sure the API is running on http://localhost:8001"
echo ""

# Use Python 3.12 Streamlit (has pyvis installed)
/Library/Frameworks/Python.framework/Versions/3.12/bin/streamlit run streamlit_app.py --server.port 8501 --server.address localhost
