#!/usr/bin/env python3
"""
Generate SHA256 hash files for pickle files
Run this after building/regenerating pickle files to create integrity hashes
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.utils.pickle_security import save_pickle_with_hash, compute_file_hash
import pickle


def generate_hash_for_existing_pickle(pickle_path: Path):
    """Generate hash file for existing pickle without re-saving"""
    if not pickle_path.exists():
        print(f"❌ File not found: {pickle_path}")
        return False

    hash_file = Path(str(pickle_path) + '.sha256')
    file_hash = compute_file_hash(pickle_path)

    with open(hash_file, 'w') as f:
        f.write(file_hash)

    print(f"✅ Generated hash for {pickle_path.name}")
    print(f"   Hash: {file_hash[:16]}...")
    print(f"   Saved to: {hash_file.name}")
    return True


def main():
    """Generate hashes for all pickle files in data directory"""
    print("=" * 60)
    print("PICKLE HASH GENERATOR")
    print("=" * 60)
    print()

    data_dir = Path(__file__).parent.parent / "data"

    if not data_dir.exists():
        print(f"❌ Data directory not found: {data_dir}")
        return 1

    pickle_files = [
        data_dir / "model.pkl",
        data_dir / "knowledge_graph.pkl",
        data_dir / "bm25_pageindex.pkl",
    ]

    success_count = 0
    for pickle_file in pickle_files:
        if generate_hash_for_existing_pickle(pickle_file):
            success_count += 1
        print()

    print("=" * 60)
    print(f"Generated {success_count}/{len(pickle_files)} hash files")
    print("=" * 60)
    print()

    if success_count < len(pickle_files):
        print("⚠️  Some pickle files are missing. Run the following to generate them:")
        print("   - python3 scripts/build_bm25.py")
        print("   - python3 scripts/build_dashboard_graph.py")
        print("   - Train and save model (if applicable)")
        return 1

    print("✅ All pickle files have integrity hashes")
    print()
    print("Next steps:")
    print("1. Commit the .sha256 files to version control")
    print("2. The API will verify pickle integrity on startup")
    print("3. Re-run this script after regenerating any pickle files")

    return 0


if __name__ == "__main__":
    sys.exit(main())
