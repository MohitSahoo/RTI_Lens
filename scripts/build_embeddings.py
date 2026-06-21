#!/usr/bin/env python3
"""
Build Vector Embeddings for Semantic Search
Embeds all markdown documents using PageIndex-aware chunking and stores in MongoDB
"""
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
from tqdm import tqdm
import numpy as np

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pymongo import MongoClient, ASCENDING
from sentence_transformers import SentenceTransformer
from backend.config import (
    MONGODB_URI,
    MONGODB_DB,
    MONGODB_COLLECTION,
    MONGODB_VECTOR_INDEX,
    EMBEDDING_MODEL,
    EMBEDDING_DIMENSION
)
from backend.database import SessionLocal
from backend.models import Case
from sqlalchemy import text

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
MD_DIR = Path("data/cic_orders_md")
PAGEINDEX_DIR = Path("data/pageindex_trees")
MAPPING_FILE = Path("data/order_number_mapping.json")


class EmbeddingBuilder:
    """Build and store document embeddings with PageIndex-aware chunking"""

    def __init__(self):
        self.model = SentenceTransformer(EMBEDDING_MODEL)
        self.client = MongoClient(MONGODB_URI)
        self.db = self.client[MONGODB_DB]
        self.collection = self.db[MONGODB_COLLECTION]
        self.order_mapping = self._load_mapping()
        self.case_metadata = self._load_case_metadata()

        logger.info(f"Loaded embedding model: {EMBEDDING_MODEL}")
        logger.info(f"Connected to MongoDB: {MONGODB_DB}.{MONGODB_COLLECTION}")

    def _load_mapping(self) -> Dict[str, str]:
        """Load order_number to hash mapping"""
        if MAPPING_FILE.exists():
            with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
                mapping = json.load(f)
                logger.info(f"Loaded {len(mapping)} order number mappings")
                return mapping
        else:
            logger.warning("order_number_mapping.json not found")
            return {}

    def _load_case_metadata(self) -> Dict[str, Dict]:
        """Load case metadata from database"""
        db = SessionLocal()
        try:
            query = text("""
                SELECT
                    c.order_number,
                    c.section_cited,
                    c.appeal_outcome,
                    c.appeal_level,
                    c.order_date,
                    m.name as ministry
                FROM cases c
                JOIN ministries m ON c.ministry_id = m.id
            """)
            results = db.execute(query).fetchall()

            metadata = {}
            for row in results:
                # Handle order_date - might be string or date object
                order_date = row.order_date
                if order_date and hasattr(order_date, 'isoformat'):
                    order_date = order_date.isoformat()

                metadata[row.order_number] = {
                    "ministry": row.ministry,
                    "section_cited": row.section_cited,
                    "appeal_outcome": row.appeal_outcome,
                    "appeal_level": row.appeal_level,
                    "order_date": order_date
                }

            logger.info(f"Loaded metadata for {len(metadata)} cases")
            return metadata
        finally:
            db.close()

    def get_order_number_from_hash(self, order_hash: str) -> Optional[str]:
        """Reverse lookup: hash to order_number"""
        for order_num, hash_val in self.order_mapping.items():
            if hash_val == order_hash:
                return order_num
        return None

    def load_pageindex_tree(self, order_hash: str) -> Optional[Dict]:
        """Load PageIndex tree for document"""
        tree_path = PAGEINDEX_DIR / f"{order_hash}.json"
        if not tree_path.exists():
            return None

        with open(tree_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def extract_section_text(self, md_path: Path, start_line: int, end_line: Optional[int] = None) -> str:
        """Extract text from markdown between line numbers"""
        if not md_path.exists():
            return ""

        with open(md_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        if end_line is None:
            end_line = len(lines)

        section_lines = lines[start_line-1:end_line]
        return ''.join(section_lines).strip()

    def chunk_document_with_pageindex(self, order_hash: str) -> List[Dict]:
        """
        Chunk document using sliding window (500 words with 100 overlap)
        """
        md_path = MD_DIR / f"{order_hash}.md"

        if not md_path.exists():
            logger.warning(f"Markdown file not found: {order_hash}.md")
            return []

        with open(md_path, 'r', encoding='utf-8') as f:
            full_text = f.read()

        # Try to extract clean title
        title = "Central Information Commission"
        lines = [line.strip() for line in full_text.split('\n') if line.strip()]
        for line in lines[:5]:
            if "vs" in line.lower() or "v." in line.lower():
                title = line.strip("# ")
                break

        # Chunk by words: 500 words with 100 overlap
        words = full_text.split()
        chunks = []
        chunk_size = 500
        overlap = 100
        
        if len(words) <= chunk_size:
            chunks = [full_text]
        else:
            i = 0
            while i < len(words):
                chunk_words = words[i:i + chunk_size]
                chunks.append(" ".join(chunk_words))
                if i + chunk_size >= len(words):
                    break
                i += chunk_size - overlap

        ret_chunks = []
        for idx, chunk_text in enumerate(chunks):
            ret_chunks.append({
                "text": chunk_text,
                "title": title,
                "hierarchy": f"Central Information Commission > {title} > Chunk {idx+1}",
                "depth": 1,
                "line_num": idx * 400
            })

        return ret_chunks

    def embed_chunks(self, chunks: List[Dict]) -> List[np.ndarray]:
        """Generate embeddings for all chunks"""
        texts = [chunk["text"] for chunk in chunks]
        embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        return embeddings

    def process_document(self, order_hash: str) -> int:
        """Process a single document and store embeddings"""
        # Get order number and metadata
        order_number = self.get_order_number_from_hash(order_hash)
        if not order_number:
            logger.warning(f"No order number found for hash: {order_hash}")
            return 0

        metadata = self.case_metadata.get(order_number, {})

        # Chunk document
        chunks = self.chunk_document_with_pageindex(order_hash)
        if not chunks:
            logger.warning(f"No chunks extracted for: {order_number}")
            return 0

        # Generate embeddings
        embeddings = self.embed_chunks(chunks)

        # Prepare documents for MongoDB
        documents = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            doc = {
                "order_number": order_number,
                "order_hash": order_hash,
                "ministry": metadata.get("ministry", "Unknown"),
                "section_cited": metadata.get("section_cited"),
                "appeal_outcome": metadata.get("appeal_outcome"),
                "appeal_level": metadata.get("appeal_level"),
                "order_date": metadata.get("order_date"),
                "text": chunk["text"],
                "title": chunk["title"],
                "hierarchy": chunk["hierarchy"],
                "depth": chunk["depth"],
                "line_num": chunk["line_num"],
                "chunk_index": i,
                "embedding": embedding.tolist()
            }
            documents.append(doc)

        # Insert into MongoDB
        if documents:
            self.collection.insert_many(documents)

        return len(documents)

    def build_index(self):
        """Create MongoDB indexes for efficient querying"""
        logger.info("Creating MongoDB indexes...")

        self.collection.create_index([("order_number", ASCENDING)])
        self.collection.create_index([("order_hash", ASCENDING)])
        self.collection.create_index([("ministry", ASCENDING)])
        self.collection.create_index([("section_cited", ASCENDING)])
        self.collection.create_index([("order_date", ASCENDING)])

        try:
            self.db.command({
                "createSearchIndexes": MONGODB_COLLECTION,
                "indexes": [
                    {
                        "name": MONGODB_VECTOR_INDEX,
                        "type": "vectorSearch",
                        "definition": {
                            "fields": [
                                {
                                    "type": "vector",
                                    "path": "embedding",
                                    "numDimensions": EMBEDDING_DIMENSION,
                                    "similarity": "cosine"
                                },
                                {"type": "filter", "path": "ministry"},
                                {"type": "filter", "path": "section_cited"},
                                {"type": "filter", "path": "order_date"},
                                {"type": "filter", "path": "appeal_outcome"}
                            ]
                        }
                    }
                ]
            })
            logger.info("Created MongoDB vector search index '%s'", MONGODB_VECTOR_INDEX)
        except Exception as e:
            logger.warning(
                "Could not create MongoDB vector search index '%s': %s. "
                "If you are on Atlas, create it manually or rerun after enabling Search.",
                MONGODB_VECTOR_INDEX,
                e
            )

        logger.info("Indexes created successfully")

    def clear_collection(self):
        """Clear existing embeddings"""
        count = self.collection.count_documents({})
        if count > 0:
            logger.info(f"Clearing {count} existing documents...")
            self.collection.delete_many({})

    def build_all(self):
        """Build embeddings for all documents"""
        self.clear_collection()

        # Get all markdown files
        md_files = list(MD_DIR.glob("*.md"))
        logger.info(f"Found {len(md_files)} markdown files")

        total_chunks = 0
        processed = 0
        failed = 0

        # Process each document
        for md_file in tqdm(md_files, desc="Embedding documents"):
            order_hash = md_file.stem

            # Skip if already embedded
            if self.collection.count_documents({"order_hash": order_hash}) > 0:
                processed += 1
                continue

            try:
                chunks_count = self.process_document(order_hash)
                total_chunks += chunks_count
                processed += 1
            except Exception as e:
                logger.error(f"Failed to process {order_hash}: {e}")
                failed += 1

        # Build indexes
        self.build_index()

        # Summary
        logger.info("=" * 60)
        logger.info("Embedding Generation Complete")
        logger.info(f"Documents processed: {processed}")
        logger.info(f"Documents failed: {failed}")
        logger.info(f"Total chunks embedded: {total_chunks}")
        logger.info(f"Average chunks per document: {total_chunks / processed if processed > 0 else 0:.1f}")
        logger.info(f"MongoDB collection: {MONGODB_DB}.{MONGODB_COLLECTION}")
        logger.info("=" * 60)

    def close(self):
        """Close MongoDB connection"""
        self.client.close()


def main():
    """Main entry point"""
    logger.info("Starting embedding generation...")
    logger.info(f"Embedding model: {EMBEDDING_MODEL}")
    logger.info(f"Embedding dimension: {EMBEDDING_DIMENSION}")

    builder = EmbeddingBuilder()

    try:
        builder.build_all()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        builder.close()


if __name__ == "__main__":
    main()
