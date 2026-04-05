"""
Build mapping from order_number to file hash for PageIndex
Output: data/order_number_mapping.json
"""
import json
import re
from pathlib import Path
from tqdm import tqdm

TXT_DIR = Path("data/cic_orders_txt")
OUTPUT_PATH = Path("data/order_number_mapping.json")

print("Building order_number to hash mapping...")

mapping = {}

for txt_file in tqdm(sorted(TXT_DIR.glob("*.txt"))):
    order_hash = txt_file.stem

    # Read first 500 lines to find order number
    try:
        with open(txt_file, 'r', encoding='utf-8') as f:
            content = ''.join(f.readlines()[:500])

        # Look for patterns like "File No : CIC/..." or "CIC/..."
        match = re.search(r'(CIC/[A-Z]+/[A-Z]/\d{4}/\d+)', content)
        if match:
            order_number = match.group(1)
            mapping[order_number] = order_hash
    except Exception as e:
        print(f"\nWarning: Failed to process {txt_file.name}: {e}")
        continue

print(f"\nFound {len(mapping)} order numbers")

# Save mapping
with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    json.dump(mapping, f, indent=2)

print(f"Mapping saved to {OUTPUT_PATH}")
