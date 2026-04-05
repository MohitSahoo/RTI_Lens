"""
Runs VectifyAI PageIndex on every TXT file to produce
a hierarchical tree JSON per order. Saved to data/pageindex_trees/.
"""

import sys
import json
import subprocess
import os
import shutil
from pathlib import Path
from tqdm import tqdm

MD_DIR    = Path("data/cic_orders_md")
TREE_DIR  = Path("data/pageindex_trees")
RESULTS_DIR = Path("results")
TREE_DIR.mkdir(exist_ok=True)

md_files = sorted(MD_DIR.glob("*.md"))
print(f"Building PageIndex trees for {len(md_files)} files...")

for md_path in tqdm(md_files):
    tree_path = TREE_DIR / f"{md_path.stem}.json"
    if tree_path.exists():
        continue  # already processed

    pageindex_output = RESULTS_DIR / f"{md_path.stem}_structure.json"

    # Run PageIndex with the markdown file (saves to results/ by default)
    result = subprocess.run(
        ["python3", "pageindex_lib/run_pageindex.py",
         "--md_path", str(md_path)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"\nWarning: PageIndex failed for {md_path.name}: {result.stderr[:200]}")
    else:
        # Move the output file to our target directory
        if pageindex_output.exists():
            shutil.move(str(pageindex_output), str(tree_path))

print(f"Done. Trees saved to {TREE_DIR}/")
