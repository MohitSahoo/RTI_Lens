#!/usr/bin/env python3
"""
Complete Rebuild Script - From JSONL to Full System with Vector Embeddings
Processes clean_cases_final_balanced.jsonl and rebuilds:
1. PostgreSQL database (cases, ministries, paragraphs)
2. Markdown files
3. MongoDB documents
4. PageIndex trees
5. BM25 index
6. Vector embeddings in MongoDB
"""

import sys
import json
import logging
import subprocess
import hashlib
from pathlib import Path
from typing import Dict, List
from tqdm import tqdm
from pymongo import MongoClient
from sqlalchemy import create_engine, text
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
JSONL_FILE = Path("clean_cases_final_balanced.jsonl")
MD_DIR = Path("data/cic_orders_md")
TREE_DIR = Path("data/pageindex_trees")
MAPPING_FILE = Path("data/order_number_mapping.json")

# Database connections
MONGODB_URI = "mongodb://localhost:27017/"
POSTGRES_URL = "postgresql://mohitsahoo@localhost:5432/rtilens"

# Create directories
MD_DIR.mkdir(parents=True, exist_ok=True)
TREE_DIR.mkdir(parents=True, exist_ok=True)


class RebuildOrchestrator:
    """Orchestrates the complete rebuild process"""

    def __init__(self):
        self.mongo_client = MongoClient(MONGODB_URI)
        self.mongo_db = self.mongo_client['rti_lens']
        self.pg_engine = create_engine(POSTGRES_URL)
        self.order_mapping = {}
        self.ministry_cache = {}
        self.processed_count = 0

    def generate_hash(self, order_number: str) -> str:
        """Generate MD5 hash for order number"""
        return hashlib.md5(order_number.encode()).hexdigest()

    def get_or_create_ministry(self, ministry_name: str) -> int:
        """Get or create ministry in PostgreSQL"""
        if not ministry_name or ministry_name == "Unknown":
            ministry_name = "Unknown Ministry"

        # Check cache
        if ministry_name in self.ministry_cache:
            return self.ministry_cache[ministry_name]

        with self.pg_engine.connect() as conn:
            # Try to find existing
            result = conn.execute(
                text("SELECT id FROM ministries WHERE name = :name"),
                {"name": ministry_name}
            ).fetchone()

            if result:
                ministry_id = result[0]
            else:
                # Create new
                result = conn.execute(
                    text("INSERT INTO ministries (name) VALUES (:name) RETURNING id"),
                    {"name": ministry_name}
                )
                ministry_id = result.fetchone()[0]
                conn.commit()

            self.ministry_cache[ministry_name] = ministry_id
            return ministry_id

    def step1_process_jsonl_to_postgres(self):
        """Step 1: Process JSONL and populate PostgreSQL database"""
        logger.info("="*60)
        logger.info("STEP 1: Processing JSONL to PostgreSQL")
        logger.info("="*60)

        if not JSONL_FILE.exists():
            logger.error(f"JSONL file not found: {JSONL_FILE}")
            return False

        # Clear existing data
        logger.info("Clearing PostgreSQL tables...")
        with self.pg_engine.connect() as conn:
            conn.execute(text("DELETE FROM paragraphs"))
            conn.execute(text("DELETE FROM cases"))
            conn.commit()
        logger.info("PostgreSQL tables cleared")

        # Load JSONL
        logger.info(f"Reading {JSONL_FILE}...")
        with open(JSONL_FILE, 'r', encoding='utf-8') as f:
            cases = [json.loads(line) for line in f]

        logger.info(f"Found {len(cases)} cases")

        # Process each case
        for case in tqdm(cases, desc="Ingesting to PostgreSQL"):
            try:
                self._ingest_case_to_postgres(case)
                self.processed_count += 1
            except Exception as e:
                logger.error(f"Error ingesting case {case.get('case_id')}: {str(e)}")
                continue

        logger.info(f"✅ Step 1 complete: {self.processed_count} cases ingested to PostgreSQL")
        return True

    def _ingest_case_to_postgres(self, case: Dict):
        """Ingest a single case into PostgreSQL"""
        metadata = case.get('metadata', {})

        # Extract fields
        order_number = metadata.get('order_number', case.get('case_id', 'unknown'))
        ministry_name = metadata.get('ministry', 'Unknown Ministry')
        section_cited = metadata.get('section_cited')
        appeal_outcome = metadata.get('appeal_outcome')
        appeal_level = metadata.get('appeal_level')
        order_date_str = metadata.get('order_date')

        # Parse date
        order_date = None
        if order_date_str:
            try:
                order_date = datetime.fromisoformat(order_date_str.replace('Z', '+00:00')).date()
            except:
                pass

        # Get ministry ID
        ministry_id = self.get_or_create_ministry(ministry_name)

        # Get text
        raw_text = case.get('clean_text') or case.get('raw_text', '')

        # Insert case
        with self.pg_engine.connect() as conn:
            result = conn.execute(
                text("""
                    INSERT INTO cases (
                        order_number, ministry_id, section_cited,
                        appeal_outcome, appeal_level, order_date,
                        extraction_method, raw_text
                    ) VALUES (
                        :order_number, :ministry_id, :section_cited,
                        :appeal_outcome, :appeal_level, :order_date,
                        'jsonl', :raw_text
                    ) RETURNING id
                """),
                {
                    "order_number": order_number,
                    "ministry_id": ministry_id,
                    "section_cited": section_cited,
                    "appeal_outcome": appeal_outcome,
                    "appeal_level": appeal_level,
                    "order_date": order_date,
                    "raw_text": raw_text
                }
            )
            case_id = result.fetchone()[0]

            # Insert paragraphs
            paragraphs = case.get('paragraphs', [])
            if isinstance(paragraphs, list):
                for idx, para in enumerate(paragraphs):
                    if isinstance(para, str) and para.strip():
                        conn.execute(
                            text("""
                                INSERT INTO paragraphs (case_id, paragraph_index, text)
                                VALUES (:case_id, :idx, :text)
                            """),
                            {"case_id": case_id, "idx": idx, "text": para.strip()}
                        )

            conn.commit()

    def step2_create_markdown_and_mongodb(self):
        """Step 2: Create markdown files and populate MongoDB"""
        logger.info("="*60)
        logger.info("STEP 2: Creating Markdown files and MongoDB documents")
        logger.info("="*60)

        # Clear MongoDB
        logger.info("Clearing MongoDB collections...")
        self.mongo_db['documents'].delete_many({})
        self.mongo_db['chunks'].delete_many({})
        self.mongo_db['document_trees'].delete_many({})

        # Load JSONL again
        with open(JSONL_FILE, 'r', encoding='utf-8') as f:
            cases = [json.loads(line) for line in f]

        # Process each case
        for case in tqdm(cases, desc="Creating markdown & MongoDB docs"):
            try:
                self._create_markdown_and_mongo(case)
            except Exception as e:
                logger.error(f"Error processing case {case.get('case_id')}: {str(e)}")
                continue

        # Save order mapping
        with open(MAPPING_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.order_mapping, f, indent=2)

        md_count = len(list(MD_DIR.glob('*.md')))
        mongo_count = self.mongo_db['documents'].count_documents({})

        logger.info(f"✅ Step 2 complete:")
        logger.info(f"   - Markdown files: {md_count}")
        logger.info(f"   - MongoDB documents: {mongo_count}")
        return True

    def _create_markdown_and_mongo(self, case: Dict):
        """Create markdown file and MongoDB document for a case"""
        case_id = case.get('case_id', 'unknown')
        metadata = case.get('metadata', {})
        order_number = metadata.get('order_number', case_id)

        # Generate hash
        order_hash = self.generate_hash(order_number)
        self.order_mapping[order_number] = order_hash

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

        self.mongo_db['documents'].insert_one(doc)

    def step3_build_pageindex(self):
        """Step 3: Build PageIndex trees"""
        logger.info("="*60)
        logger.info("STEP 3: Building PageIndex trees")
        logger.info("="*60)

        try:
            result = subprocess.run(
                [sys.executable, "scripts/build_pageindex.py"],
                capture_output=True,
                text=True,
                timeout=3600
            )

            if result.returncode == 0:
                tree_count = len(list(TREE_DIR.glob("*.json")))
                logger.info(f"✅ Step 3 complete: {tree_count} PageIndex trees built")
                return True
            else:
                logger.warning(f"PageIndex build had issues: {result.stderr[:500]}")
                tree_count = len(list(TREE_DIR.glob("*.json")))
                logger.info(f"   Created {tree_count} trees (some may have failed)")
                return tree_count > 0

        except Exception as e:
            logger.error(f"Error building PageIndex: {str(e)}")
            return False

    def step4_build_bm25(self):
        """Step 4: Build BM25 index"""
        logger.info("="*60)
        logger.info("STEP 4: Building BM25 index")
        logger.info("="*60)

        try:
            result = subprocess.run(
                [sys.executable, "scripts/build_bm25.py"],
                capture_output=True,
                text=True,
                timeout=600
            )

            if result.returncode == 0:
                bm25_path = Path("data/bm25_pageindex.pkl")
                if bm25_path.exists():
                    size_mb = bm25_path.stat().st_size / (1024 * 1024)
                    logger.info(f"✅ Step 4 complete: BM25 index built ({size_mb:.1f} MB)")
                    return True

            logger.error(f"BM25 build failed: {result.stderr[:500]}")
            return False

        except Exception as e:
            logger.error(f"Error building BM25: {str(e)}")
            return False

    def step5_build_embeddings(self):
        """Step 5: Build vector embeddings and store in MongoDB"""
        logger.info("="*60)
        logger.info("STEP 5: Building vector embeddings for MongoDB")
        logger.info("="*60)

        try:
            result = subprocess.run(
                [sys.executable, "scripts/build_embeddings.py"],
                capture_output=True,
                text=True,
                timeout=7200
            )

            if result.returncode == 0:
                # Check MongoDB for embeddings
                db_vectors = self.mongo_client['rtilens_vectors']
                embedding_count = db_vectors['document_embeddings'].count_documents({})
                logger.info(f"✅ Step 5 complete: {embedding_count} embeddings created in MongoDB")
                return True
            else:
                logger.error(f"Embeddings build failed: {result.stderr[:500]}")
                return False

        except Exception as e:
            logger.error(f"Error building embeddings: {str(e)}")
            return False

    def run_full_rebuild(self):
        """Run complete rebuild process"""
        logger.info("="*60)
        logger.info("RTI-Lens Complete Rebuild from JSONL")
        logger.info("="*60)
        logger.info(f"Source: {JSONL_FILE}")

        # Count cases
        with open(JSONL_FILE, 'r') as f:
            case_count = sum(1 for _ in f)

        logger.info(f"Cases: {case_count}")
        logger.info("="*60)
        logger.info("\nThis will:")
        logger.info("  1. Ingest to PostgreSQL (cases, ministries, paragraphs)")
        logger.info("  2. Create markdown files")
        logger.info("  3. Populate MongoDB documents")
        logger.info("  4. Build PageIndex trees")
        logger.info("  5. Build BM25 index")
        logger.info("  6. Build vector embeddings in MongoDB")
        logger.info("\nEstimated time: 30-60 minutes")

        # Confirm
        response = input("\nContinue? (yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            logger.info("Rebuild cancelled")
            return

        # Run steps
        steps = [
            ("Ingest to PostgreSQL", self.step1_process_jsonl_to_postgres),
            ("Create Markdown & MongoDB", self.step2_create_markdown_and_mongodb),
            ("Build PageIndex Trees", self.step3_build_pageindex),
            ("Build BM25 Index", self.step4_build_bm25),
            ("Build Vector Embeddings", self.step5_build_embeddings),
        ]

        results = {}
        for step_name, step_func in steps:
            logger.info(f"\n{'='*60}")
            logger.info(f"Starting: {step_name}")
            logger.info(f"{'='*60}")

            success = step_func()
            results[step_name] = success

            if not success:
                logger.error(f"❌ {step_name} failed!")
                response = input("Continue anyway? (yes/no): ").strip().lower()
                if response not in ['yes', 'y']:
                    break

        # Summary
        logger.info("\n" + "="*60)
        logger.info("REBUILD SUMMARY")
        logger.info("="*60)

        for step_name, success in results.items():
            status = "✅ SUCCESS" if success else "❌ FAILED"
            logger.info(f"{status}: {step_name}")

        # Final verification
        logger.info("\n" + "="*60)
        logger.info("VERIFICATION")
        logger.info("="*60)

        with self.pg_engine.connect() as conn:
            case_count = conn.execute(text("SELECT COUNT(*) FROM cases")).scalar()
            para_count = conn.execute(text("SELECT COUNT(*) FROM paragraphs")).scalar()
            logger.info(f"PostgreSQL: {case_count} cases, {para_count} paragraphs")

        mongo_docs = self.mongo_db['documents'].count_documents({})
        logger.info(f"MongoDB documents: {mongo_docs}")

        md_files = len(list(MD_DIR.glob('*.md')))
        logger.info(f"Markdown files: {md_files}")

        tree_files = len(list(TREE_DIR.glob('*.json')))
        logger.info(f"PageIndex trees: {tree_files}")

        bm25_exists = Path("data/bm25_pageindex.pkl").exists()
        logger.info(f"BM25 index: {'✅ exists' if bm25_exists else '❌ missing'}")

        db_vectors = self.mongo_client['rtilens_vectors']
        embedding_count = db_vectors['document_embeddings'].count_documents({})
        logger.info(f"Vector embeddings: {embedding_count} chunks in MongoDB")

        if all(results.values()):
            logger.info("\n🎉 Complete rebuild successful!")
            logger.info("\nSystem is ready:")
            logger.info("  - PostgreSQL: Cases and paragraphs")
            logger.info("  - MongoDB: Documents and vector embeddings")
            logger.info("  - Files: Markdown and PageIndex trees")
            logger.info("  - Indexes: BM25 for keyword search")
            logger.info("\nNext: Start the API and Streamlit frontend")
        else:
            logger.warning("\n⚠️ Some steps failed. Check logs above.")

        self.mongo_client.close()


def main():
    """Main entry point"""
    try:
        orchestrator = RebuildOrchestrator()
        orchestrator.run_full_rebuild()
    except KeyboardInterrupt:
        logger.info("\n\nRebuild interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n\nRebuild failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
