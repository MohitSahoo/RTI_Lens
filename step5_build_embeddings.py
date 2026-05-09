#!/usr/bin/env python3
"""
Step 5: Build Vector Embeddings
Creates semantic embeddings and stores in MongoDB
"""

import sys
from pathlib import Path

print("="*60)
print("STEP 5: Build Vector Embeddings")
print("="*60)

print("\nRunning existing embeddings script...")
print("This will take 15-30 minutes...")

import subprocess
result = subprocess.run(
    [sys.executable, "scripts/build_embeddings.py"],
    capture_output=False,
    text=True
)

if result.returncode == 0:
    print("\n" + "="*60)
    print("STEP 5 COMPLETE")
    print("="*60)
    print("✓ Vector embeddings created in MongoDB")
else:
    print("\n" + "="*60)
    print("STEP 5 FAILED")
    print("="*60)
    print("Check error messages above")
    sys.exit(1)
