#!/usr/bin/env python3
"""
Complete Database Cleanup Script
Cleans PostgreSQL, MongoDB, and files before rebuild
"""

import sys
import logging
from pathlib import Path
from pymongo import MongoClient
from sqlalchemy import create_engine, text

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database connections
MONGODB_URI = "mongodb://localhost:27017/"
POSTGRES_URL = "postgresql://mohitsahoo@localhost:5432/rtilens"

# Paths
MD_DIR = Path("data/cic_orders_md")
TREE_DIR = Path("data/pageindex_trees")
BM25_FILE = Path("data/bm25_pageindex.pkl")


def cleanup_postgresql():
    """Clean up PostgreSQL database"""
    logger.info("="*60)
    logger.info("PostgreSQL Cleanup")
    logger.info("="*60)

    engine = create_engine(POSTGRES_URL)

    try:
        with engine.connect() as conn:
            # Get counts before deletion
            logger.info("\nCurrent data:")

            tables = [
                ('workflow_actions', 'Workflow actions'),
                ('workflow_sessions', 'Workflow sessions'),
                ('paragraphs', 'Paragraphs'),
                ('cases', 'Cases'),
                ('section_stats', 'Section stats'),
                ('ministry_stats', 'Ministry stats'),
                ('ministries', 'Ministries')
            ]

            for table, description in tables:
                try:
                    count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                    logger.info(f"  {description}: {count}")
                except Exception as e:
                    logger.debug(f"  {description}: table not found or error")

            # Delete in correct order (respecting foreign keys)
            logger.info("\nDeleting data...")

            delete_order = [
                ('workflow_actions', 'Workflow actions'),
                ('workflow_sessions', 'Workflow sessions'),
                ('paragraphs', 'Paragraphs'),
                ('section_stats', 'Section stats'),
                ('ministry_stats', 'Ministry stats'),
                ('cases', 'Cases'),
                ('ministries', 'Ministries')
            ]

            for table, description in delete_order:
                try:
                    result = conn.execute(text(f"DELETE FROM {table}"))
                    conn.commit()
                    logger.info(f"  ✅ Cleared {description}")
                except Exception as e:
                    logger.warning(f"  ⚠️  {description}: {str(e)[:100]}")

            logger.info("\n✅ PostgreSQL cleanup complete")
            return True

    except Exception as e:
        logger.error(f"PostgreSQL cleanup failed: {str(e)}")
        return False
    finally:
        engine.dispose()


def cleanup_mongodb():
    """Clean up MongoDB collections"""
    logger.info("="*60)
    logger.info("MongoDB Cleanup")
    logger.info("="*60)

    try:
        client = MongoClient(MONGODB_URI)

        # Database 1: rti_lens
        db_rti = client['rti_lens']
        collections_rti = ['documents', 'chunks', 'document_trees']

        logger.info("\nDatabase: rti_lens")
        for coll in collections_rti:
            count = db_rti[coll].count_documents({})
            logger.info(f"  {coll}: {count} documents")
            result = db_rti[coll].delete_many({})
            logger.info(f"    ✅ Deleted {result.deleted_count} documents")

        # Database 2: rtilens_vectors
        db_vectors = client['rtilens_vectors']
        count = db_vectors['document_embeddings'].count_documents({})
        logger.info(f"\nDatabase: rtilens_vectors")
        logger.info(f"  document_embeddings: {count} documents")
        result = db_vectors['document_embeddings'].delete_many({})
        logger.info(f"    ✅ Deleted {result.deleted_count} documents")

        client.close()
        logger.info("\n✅ MongoDB cleanup complete")
        return True

    except Exception as e:
        logger.error(f"MongoDB cleanup failed: {str(e)}")
        return False


def cleanup_files():
    """Clean up markdown files, PageIndex trees, and BM25 index"""
    logger.info("="*60)
    logger.info("File Cleanup")
    logger.info("="*60)

    deleted_counts = {
        'markdown': 0,
        'trees': 0,
        'bm25': 0
    }

    # Clean markdown files
    if MD_DIR.exists():
        md_files = list(MD_DIR.glob("*.md"))
        logger.info(f"\nMarkdown files: {len(md_files)}")
        for f in md_files:
            f.unlink()
            deleted_counts['markdown'] += 1
        logger.info(f"  ✅ Deleted {deleted_counts['markdown']} files")

    # Clean PageIndex trees
    if TREE_DIR.exists():
        tree_files = list(TREE_DIR.glob("*.json"))
        logger.info(f"\nPageIndex trees: {len(tree_files)}")
        for f in tree_files:
            f.unlink()
            deleted_counts['trees'] += 1
        logger.info(f"  ✅ Deleted {deleted_counts['trees']} files")

    # Clean BM25 index
    if BM25_FILE.exists():
        size_mb = BM25_FILE.stat().st_size / (1024 * 1024)
        logger.info(f"\nBM25 index: {size_mb:.1f} MB")
        BM25_FILE.unlink()
        deleted_counts['bm25'] = 1
        logger.info(f"  ✅ Deleted BM25 index")

    logger.info("\n✅ File cleanup complete")
    return True


def main():
    """Main cleanup function"""
    logger.info("="*60)
    logger.info("RTI-Lens Complete Database Cleanup")
    logger.info("="*60)

    logger.info("\nThis will DELETE ALL DATA from:")
    logger.info("  - PostgreSQL (cases, ministries, paragraphs, workflows)")
    logger.info("  - MongoDB (documents, embeddings, trees)")
    logger.info("  - Files (markdown, PageIndex trees, BM25 index)")
    logger.info("\nSchema and structure will be kept intact.")

    response = input("\n⚠️  Are you sure? Type 'yes' to continue: ").strip().lower()
    if response != 'yes':
        logger.info("Cleanup cancelled")
        return 1

    # Run cleanup
    results = {
        'PostgreSQL': cleanup_postgresql(),
        'MongoDB': cleanup_mongodb(),
        'Files': cleanup_files()
    }

    # Summary
    logger.info("\n" + "="*60)
    logger.info("CLEANUP SUMMARY")
    logger.info("="*60)

    for component, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        logger.info(f"{status}: {component}")

    if all(results.values()):
        logger.info("\n🎉 Complete cleanup successful!")
        logger.info("\nDatabase is now empty and ready for rebuild.")
        logger.info("\nNext step: Run rebuild_from_jsonl.py")
        return 0
    else:
        logger.warning("\n⚠️ Some cleanup operations failed")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("\n\nCleanup interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n\nCleanup failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
