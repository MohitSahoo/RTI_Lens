#!/bin/bash
# Serve HTML frontend for RTI-Lens

echo "Starting RTI-Lens HTML Frontend..."
echo "Make sure the API is running on http://localhost:8001"
echo ""
echo "Opening frontend at http://localhost:8002"
echo ""

python3 -m http.server 8002
