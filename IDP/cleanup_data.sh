#!/bin/bash
# Quick cleanup script for Linux/Mac
# Cleans MongoDB and PageIndex trees

echo ""
echo "========================================"
echo "RTI-Lens Data Cleanup"
echo "========================================"
echo ""
echo "This will delete:"
echo "  - All MongoDB documents"
echo "  - All PageIndex tree files"
echo "  - BM25 index file"
echo ""
echo "Schema and structure will be kept intact."
echo ""

read -p "Press Enter to continue or Ctrl+C to cancel..."

python3 cleanup_data.py
