"""
Synchronize PageIndex trees and Markdown files with the database.
Removes orphaned files that were not ingested into the 'cases' table.
Ensures 1-to-1 mapping between database records and disk files.
"""
import os
import json
import re
from pathlib import Path
from sqlalchemy import create_engine, text

DB_URL = "postgresql://mohitsahoo@localhost:5432/rtilens"
MD_DIR = Path("data/cic_orders_md")
TREE_DIR = Path("data/pageindex_trees")
MAPPING_FILE = Path("data/order_number_mapping.json")
TXT_DIR = Path("data/cic_orders_txt")

def sync():
    engine = create_engine(DB_URL)
    
    print("Fetching valid order numbers from database...")
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT order_number FROM cases")).fetchall()
        db_order_numbers = {row[0] for row in rows}
    
    print(f"Found {len(db_order_numbers)} unique cases in database.")

    valid_hashes = set()
    gold_mapping = {}
    found_order_numbers = set()

    print("Identifying the best file match for each database record...")
    # Sort files so we pick consistently (e.g. first alphabetically)
    for txt_file in sorted(TXT_DIR.glob("*.txt")):
        stem = txt_file.stem
        try:
            with open(txt_file, 'r', encoding='utf-8') as f:
                content = f.read(2000)
            
            # Match order number pattern
            match = re.search(r'(CIC/[A-Z]+/[A-Z]/\d{4}/\d+)', content)
            order_number = match.group(1) if match else stem
            
            if order_number in db_order_numbers and order_number not in found_order_numbers:
                valid_hashes.add(stem)
                gold_mapping[order_number] = stem
                found_order_numbers.add(order_number)
        except:
            continue

    print(f"Matched {len(valid_hashes)} files to {len(db_order_numbers)} database records.")

    # Prune Trees
    print("Pruning PageIndex trees...")
    tree_count = 0
    deleted_trees = 0
    for tree_file in TREE_DIR.glob("*.json"):
        if tree_file.stem not in valid_hashes:
            tree_file.unlink()
            deleted_trees += 1
    
    # Prune Markdown
    print("Pruning Markdown files...")
    deleted_md = 0
    for md_file in MD_DIR.glob("*.md"):
        if md_file.stem not in valid_hashes:
            md_file.unlink()
            deleted_md += 1

    # Update Mapping
    print("Updating order_number_mapping.json...")
    with open(MAPPING_FILE, 'w', encoding='utf-8') as f:
        json.dump(gold_mapping, f, indent=2)

    remaining_trees = len(list(TREE_DIR.glob('*.json')))
    print(f"\nSync Complete!")
    print(f"- Deleted {deleted_trees} orphaned/duplicate trees.")
    print(f"- Deleted {deleted_md} orphaned/duplicate markdown files.")
    print(f"- Updated mapping with {len(gold_mapping)} entries.")
    print(f"- Total PageIndex trees remaining: {remaining_trees}")
    
    if remaining_trees != len(db_order_numbers):
        print(f"Note: {len(db_order_numbers) - remaining_trees} cases in DB still lack matching files on disk.")

if __name__ == "__main__":
    sync()
