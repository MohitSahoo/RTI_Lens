"""
Converts plain text CIC orders to markdown format by detecting headers.
This allows PageIndex to properly extract hierarchical structure.
"""

import re
from pathlib import Path
from tqdm import tqdm

TXT_DIR = Path("data/cic_orders_txt")
MD_DIR = Path("data/cic_orders_md")
MD_DIR.mkdir(exist_ok=True)

def is_header(line, next_line=None):
    """Detect if a line is likely a header."""
    line = line.strip()

    # Skip empty lines
    if not line:
        return False, 0

    # Main title patterns (H1)
    if "Central Information Commission" in line:
        return True, 1
    if re.match(r'^[A-Z\s]{10,}$', line) and len(line) < 60:
        return True, 1

    # Section headers (H2)
    if line.endswith(':') and len(line) < 50:
        return True, 2
    if re.match(r'^(Information sought|Relevant facts|Decision|Order|Appeal|Complaint)', line, re.IGNORECASE):
        return True, 2

    # Sub-headers (H3)
    if line.startswith('Note') and line.endswith(':'):
        return True, 3

    return False, 0

def convert_to_markdown(txt_path):
    """Convert a plain text file to markdown format."""
    with open(txt_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    md_lines = []
    for i, line in enumerate(lines):
        next_line = lines[i+1] if i+1 < len(lines) else None

        is_hdr, level = is_header(line, next_line)
        if is_hdr and line.strip():
            # Add markdown header
            md_lines.append(f"{'#' * level} {line.strip()}\n\n")
        elif line.strip():
            # Regular content
            md_lines.append(line)
        else:
            # Preserve empty lines
            md_lines.append(line)

    return ''.join(md_lines)

# Process all files
txt_files = sorted(TXT_DIR.glob("*.txt"))
print(f"Converting {len(txt_files)} TXT files to Markdown...")

for txt_path in tqdm(txt_files):
    md_path = MD_DIR / f"{txt_path.stem}.md"

    # Convert to markdown
    md_content = convert_to_markdown(txt_path)

    # Save markdown file
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_content)

print(f"Done. Markdown files saved to {MD_DIR}/")
