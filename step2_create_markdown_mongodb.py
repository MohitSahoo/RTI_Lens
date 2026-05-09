#!/usr/bin/env python3
"""
Step 2: Create Markdown Files and MongoDB Documents
Creates markdown files and populates MongoDB from JSONL
"""

import json
import hashlib
from pathlib import Path
from pymongo import MongoClient
from tqdm import tqdm

JSONL_FILE = Path("clean_cases_final_balanced.jsonl")
MD_DIR = Path("data/cic_orders_md")
MAPPING_FILE = Path("data/order_number_mapping.json")
MONGODB_URI = "mongodb://localhost:27017/"

print("="*60)
print("STEP 2: Create Markdown & MongoDB Documents")
print("="*60)

# Create directories
MD_DIR.mkdir(parents=True, exist_ok=True)

# Connect to MongoDB
client = MongoClient(MONGODB_URI)
db = client['rti_lens']

# Clean MongoDB
print("\nCleaning MongoDB collections...")
for coll in ['documents', 'chunks', 'document_trees']:
    count = db[coll].count_documents({})
    result = db[coll].delete_many({})
    print(f"  ✓ Cleared {coll}: {result.deleted_count} documents")

# Load JSONL
print(f"\nLoading {JSONL_FILE}...")
with open(JSONL_FILE, 'r', encoding='utf-8') as f:
    cases = [json.loads(line) for line in f]

print(f"Found {len(cases)} cases")

# Process cases
order_mapping = {}

print("\nCreating markdown files and MongoDB documents...")
for case in tqdm(cases, desc="Processing"):
    case_id = case.get('case_id', 'unknown')
    metadata = case.get('metadata', {})
    order_number = metadata.get('order_number', case_id)

    # Generate hash
    order_hash = hashlib.md5(order_number.encode()).hexdigest()
    order_mapping[order_number] = order_hash

    # Create markdown file
    md_path = MD_DIR / f"{order_hash}.md"
    content = case.get('clean_text') or case.get('raw_text', '')

    # Add metadata header
    header = f"""# {order_number}

**Ministry:** {metadata.get('ministry', 'Unknown')}
**Section:** {metadata.get('section_cited', 'N/A')}
**Date:** {metadata.get('order_date', 'N/A')}
**Outcome:** {metadata.get('appeal_outcome', 'N/A')}

---

"""

    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(header + content)

    # Store in MongoDB
    doc = {
        'order_number': order_number,
        'order_hash': order_hash,
        'case_id': case_id,
        'metadata': metadata,
        'raw_text': case.get('raw_text', ''),
        'clean_text': content,
        'paragraphs': case.get('paragraphs', []),
        'segments': case.get('segments', []),
        'quality_score': case.get('quality_score', 0),
        'quality_flags': case.get('quality_flags', [])
    }

    db['documents'].insert_one(doc)

# Save order mapping
print("\nSaving order number mapping...")
with open(MAPPING_FILE, 'w', encoding='utf-8') as f:
    json.dump(order_mapping, f, indent=2)

# Verify
md_count = len(list(MD_DIR.glob('*.md')))
mongo_count = db['documents'].count_documents({})

print("\n" + "="*60)
print("STEP 2 COMPLETE")
print("="*60)
print(f"✓ Markdown files: {md_count}")
print(f"✓ MongoDB documents: {mongo_count}")
print(f"✓ Order mapping saved: {MAPPING_FILE}")

client.close()
