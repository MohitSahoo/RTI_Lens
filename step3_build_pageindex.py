#!/usr/bin/env python3
"""
Step 3: Build PageIndex Trees
Runs PageIndex on all markdown files to create hierarchical structures
"""

import subprocess
import sys
from pathlib import Path
from tqdm import tqdm
import shutil

MD_DIR = Path("data/cic_orders_md")
TREE_DIR = Path("data/pageindex_trees")
RESULTS_DIR = Path("results")

print("="*60)
print("STEP 3: Build PageIndex Trees")
print("="*60)

# Create directories
TREE_DIR.mkdir(parents=True, exist_ok=True)

# Get markdown files
md_files = sorted(MD_DIR.glob("*.md"))
print(f"\nFound {len(md_files)} markdown files")

if len(md_files) == 0:
    print("ERROR: No markdown files found. Run Step 2 first.")
    sys.exit(1)

print("\nBuilding PageIndex trees...")
success_count = 0
skip_count = 0
error_count = 0

for md_path in tqdm(md_files, desc="Processing"):
    tree_path = TREE_DIR / f"{md_path.stem}.json"

    # Skip if already exists
    if tree_path.exists():
        skip_count += 1
        continue

    pageindex_output = RESULTS_DIR / f"{md_path.stem}_structure.json"

    # Run PageIndex
    result = subprocess.run(
        [sys.executable, "pageindex_lib/run_pageindex.py", "--md_path", str(md_path)],
        capture_output=True,
        text=True
    )

    if result.returncode == 0 and pageindex_output.exists():
        # Move to target directory
        shutil.move(str(pageindex_output), str(tree_path))
        success_count += 1
    else:
        error_count += 1

print("\n" + "="*60)
print("STEP 3 COMPLETE")
print("="*60)
print(f"✓ Successfully created: {success_count}")
print(f"⊘ Skipped (already exist): {skip_count}")
print(f"✗ Errors: {error_count}")
print(f"Total trees: {len(list(TREE_DIR.glob('*.json')))}")
