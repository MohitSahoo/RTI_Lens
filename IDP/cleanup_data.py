#!/usr/bin/env python3
"""
MongoDB and PageIndex Cleanup Script
Clears all data but keeps schema/collections intact
"""

import sys
import os
from pathlib import Path
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def print_header(text):
    """Print formatted header"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def confirm_action(message):
    """Ask user for confirmation"""
    response = input(f"\n{message} (yes/no): ").strip().lower()
    return response in ['yes', 'y']

def cleanup_mongodb():
    """Clean up MongoDB collections"""
    print_header("MongoDB Cleanup")

    # Get MongoDB connection details
    mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")

    try:
        client = MongoClient(mongodb_uri)

        # Database 1: rti_lens
        db_rti = client['rti_lens']
        collections_rti = ['documents', 'chunks', 'document_trees']

        print("\n[1/2] Database: rti_lens")
        for collection_name in collections_rti:
            collection = db_rti[collection_name]
            count = collection.count_documents({})
            print(f"  - {collection_name}: {count} documents")

        # Database 2: rtilens_vectors
        db_vectors = client['rtilens_vectors']
        collection_embeddings = db_vectors['document_embeddings']
        embeddings_count = collection_embeddings.count_documents({})

        print("\n[2/2] Database: rtilens_vectors")
        print(f"  - document_embeddings: {embeddings_count} documents")

        # Confirm deletion
        if not confirm_action("\n[WARNING] Delete all documents from these collections?"):
            print("\n[CANCELLED] MongoDB cleanup cancelled")
            return False

        # Delete documents
        print("\n[DELETING] Clearing MongoDB collections...")

        deleted_counts = {}
        for collection_name in collections_rti:
            result = db_rti[collection_name].delete_many({})
            deleted_counts[f"rti_lens.{collection_name}"] = result.deleted_count
            print(f"  [OK] Deleted {result.deleted_count} documents from rti_lens.{collection_name}")

        result = collection_embeddings.delete_many({})
        deleted_counts["rtilens_vectors.document_embeddings"] = result.deleted_count
        print(f"  [OK] Deleted {result.deleted_count} documents from rtilens_vectors.document_embeddings")

        # Verify collections still exist (schema intact)
        print("\n[VERIFY] Checking collections still exist...")
        for collection_name in collections_rti:
            if collection_name in db_rti.list_collection_names():
                print(f"  [OK] Collection rti_lens.{collection_name} still exists")

        if 'document_embeddings' in db_vectors.list_collection_names():
            print(f"  [OK] Collection rtilens_vectors.document_embeddings still exists")

        client.close()

        print("\n[SUCCESS] MongoDB cleanup completed")
        return True

    except Exception as e:
        print(f"\n[ERROR] MongoDB cleanup failed: {str(e)}")
        return False

def cleanup_pageindex_trees():
    """Clean up PageIndex tree JSON files"""
    print_header("PageIndex Trees Cleanup")

    trees_dir = Path("data/pageindex_trees")

    if not trees_dir.exists():
        print(f"\n[INFO] Directory {trees_dir} does not exist")
        return True

    # Count JSON files
    json_files = list(trees_dir.glob("*.json"))

    print(f"\n[FOUND] {len(json_files)} PageIndex tree files in {trees_dir}")

    if len(json_files) == 0:
        print("[INFO] No files to delete")
        return True

    # Show sample files
    print("\nSample files:")
    for f in json_files[:5]:
        size_kb = f.stat().st_size / 1024
        print(f"  - {f.name} ({size_kb:.1f} KB)")

    if len(json_files) > 5:
        print(f"  ... and {len(json_files) - 5} more files")

    # Confirm deletion
    if not confirm_action(f"\n[WARNING] Delete all {len(json_files)} PageIndex tree files?"):
        print("\n[CANCELLED] PageIndex cleanup cancelled")
        return False

    # Delete files
    print("\n[DELETING] Removing PageIndex tree files...")
    deleted_count = 0

    for json_file in json_files:
        try:
            json_file.unlink()
            deleted_count += 1
        except Exception as e:
            print(f"  [ERROR] Failed to delete {json_file.name}: {str(e)}")

    print(f"  [OK] Deleted {deleted_count} files")

    # Verify directory still exists
    if trees_dir.exists():
        print(f"\n[VERIFY] Directory {trees_dir} still exists (schema intact)")

    print("\n[SUCCESS] PageIndex trees cleanup completed")
    return True

def cleanup_bm25_index():
    """Clean up BM25 index file"""
    print_header("BM25 Index Cleanup")

    bm25_file = Path("data/bm25_pageindex.pkl")

    if not bm25_file.exists():
        print(f"\n[INFO] BM25 index file does not exist")
        return True

    size_mb = bm25_file.stat().st_size / (1024 * 1024)
    print(f"\n[FOUND] BM25 index: {bm25_file} ({size_mb:.1f} MB)")

    # Confirm deletion
    if not confirm_action("\n[WARNING] Delete BM25 index file?"):
        print("\n[CANCELLED] BM25 cleanup cancelled")
        return False

    # Delete file
    print("\n[DELETING] Removing BM25 index...")
    try:
        bm25_file.unlink()
        print(f"  [OK] Deleted {bm25_file}")
        print("\n[SUCCESS] BM25 index cleanup completed")
        return True
    except Exception as e:
        print(f"\n[ERROR] Failed to delete BM25 index: {str(e)}")
        return False

def main():
    """Main cleanup function"""
    print_header("RTI-Lens Data Cleanup Script")

    print("\nThis script will:")
    print("  1. Clear all documents from MongoDB collections")
    print("  2. Delete all PageIndex tree JSON files")
    print("  3. Delete BM25 index file")
    print("\nWhat will be KEPT:")
    print("  - MongoDB collections (schema)")
    print("  - Database structure")
    print("  - Directory structure")
    print("  - Configuration files")

    if not confirm_action("\n[CONFIRM] Proceed with cleanup?"):
        print("\n[CANCELLED] Cleanup cancelled by user")
        sys.exit(0)

    # Track results
    results = {
        'mongodb': False,
        'pageindex': False,
        'bm25': False
    }

    # Run cleanup operations
    results['mongodb'] = cleanup_mongodb()
    results['pageindex'] = cleanup_pageindex_trees()
    results['bm25'] = cleanup_bm25_index()

    # Final summary
    print_header("Cleanup Summary")

    print("\nResults:")
    print(f"  MongoDB:        {'[OK]' if results['mongodb'] else '[FAILED]'}")
    print(f"  PageIndex Trees: {'[OK]' if results['pageindex'] else '[FAILED]'}")
    print(f"  BM25 Index:      {'[OK]' if results['bm25'] else '[FAILED]'}")

    if all(results.values()):
        print("\n[SUCCESS] All cleanup operations completed successfully")
        print("\nNext steps:")
        print("  1. Rebuild data: python scripts/ingest.py")
        print("  2. Build BM25: python scripts/build_bm25.py")
        print("  3. Build PageIndex: python scripts/build_pageindex.py")
        print("  4. Build embeddings: python scripts/build_embeddings.py")
        return 0
    else:
        print("\n[WARNING] Some cleanup operations failed")
        print("Please review the errors above")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Cleanup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERROR] Cleanup failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
