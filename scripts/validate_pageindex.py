#!/usr/bin/env python3
"""
Validate PageIndex setup and determine if OpenAI key is needed.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Paths
PAGEINDEX_DIR = Path("data/pageindex_trees")
MD_DIR = Path("data/cic_orders_md")
MAPPING_FILE = Path("data/order_number_mapping.json")

def check_openai_key():
    """Check if OpenAI API key is configured"""
    key = os.getenv("OPENAI_API_KEY")
    return bool(key and key.strip() and key != "your_openai_api_key_here")

def check_pageindex_trees():
    """Check if PageIndex trees exist"""
    if not PAGEINDEX_DIR.exists():
        return 0, []

    trees = list(PAGEINDEX_DIR.glob("*.json"))
    return len(trees), trees

def check_source_files():
    """Check if source markdown files exist"""
    if not MD_DIR.exists():
        return 0, []

    md_files = list(MD_DIR.glob("*.md"))
    return len(md_files), md_files

def check_mapping_file():
    """Check if order number mapping exists"""
    return MAPPING_FILE.exists()

def find_missing_trees(md_files, tree_files):
    """Find markdown files without corresponding trees"""
    tree_stems = {t.stem for t in tree_files}
    md_stems = {m.stem for m in md_files}
    return md_stems - tree_stems

def main():
    print("=" * 60)
    print("PageIndex Setup Validation")
    print("=" * 60)

    # Check OpenAI key
    has_key = check_openai_key()
    print(f"\n✓ OpenAI API Key: {'CONFIGURED' if has_key else 'NOT SET'}")

    # Check source files
    md_count, md_files = check_source_files()
    print(f"✓ Source markdown files: {md_count}")

    # Check PageIndex trees
    tree_count, tree_files = check_pageindex_trees()
    print(f"✓ PageIndex trees: {tree_count}")

    # Check mapping file
    has_mapping = check_mapping_file()
    print(f"✓ Order number mapping: {'EXISTS' if has_mapping else 'MISSING'}")

    # Determine status
    print("\n" + "=" * 60)
    print("Status Analysis")
    print("=" * 60)

    if tree_count == 0:
        print("\n❌ NO PAGEINDEX TREES FOUND")
        print("   OpenAI key REQUIRED to generate trees.")
        print("   Run: python scripts/build_pageindex.py")
        sys.exit(1)

    if md_count == 0:
        print("\n⚠️  No source markdown files found")
        print("   Cannot generate PageIndex trees without source files.")
        sys.exit(1)

    # Check for missing trees
    missing = find_missing_trees(md_files, tree_files)

    if missing:
        print(f"\n⚠️  {len(missing)} markdown files missing PageIndex trees")
        if len(missing) <= 10:
            print("   Missing trees for:")
            for stem in sorted(list(missing)[:10]):
                print(f"   - {stem}.md")
        else:
            print(f"   {len(missing)} files need processing")

        if has_key:
            print("\n✓ OpenAI key configured - can regenerate missing trees")
            print("  Run: python scripts/build_pageindex.py")
        else:
            print("\n❌ OpenAI key NOT configured - cannot generate missing trees")
            print("   Set OPENAI_API_KEY in .env file")
        sys.exit(1)

    # All good
    print("\n✅ PAGEINDEX SETUP COMPLETE")
    print(f"   {tree_count} trees available for runtime use")
    print("   OpenAI key NOT needed for normal operation")
    print("   (Key only needed to regenerate trees or add new documents)")

    if not has_mapping:
        print("\n⚠️  Order number mapping missing")
        print("   System will build mapping on-the-fly (slower)")
        print("   Consider running mapping generation script")

    sys.exit(0)

if __name__ == "__main__":
    main()
