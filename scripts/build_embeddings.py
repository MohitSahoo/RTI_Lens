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
                metadata[row.order_number] = {
                    "ministry": row.ministry,
                    "section_cited": row.section_cited,
                    "appeal_outcome": row.appeal_outcome,
                    "appeal_level": row.appeal_level,
                    "order_date": row.order_date.isoformat() if row.order_date else None
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
        Chunk document using PageIndex tree structure
        Each section becomes a chunk with hierarchy metadata
        """
        tree = self.load_pageindex_tree(order_hash)
        md_path = MD_DIR / f"{order_hash}.md"

        if not md_path.exists():
            logger.warning(f"Markdown file not found: {order_hash}.md")
            return []

        chunks = []

        if tree and tree.get("structure"):
            # Use PageIndex structure for intelligent chunking
            def traverse_nodes(nodes, parent_title="", depth=0):
                for i, node in enumerate(nodes):
                    title = node.get("title", "")
                    line_num = node.get("line_num", 0)

                    # Calculate end line
                    if i + 1 < len(nodes):
                        end_line = nodes[i + 1].get("line_num", None)
                    else:
                        end_line = None

                    # Build hierarchy
                    hierarchy = f"{parent_title} > {title}" if parent_title else title

                    # Extract text
                    text = self.extract_section_text(md_path, line_num, end_line)

                    if text and len(text) > 100:  # Only substantial sections
                        chunks.append({
                            "text": text,
                            "title": title,
                            "hierarchy": hierarchy,
                            "depth": depth,
                            "line_num": line_num
                        })

                    # Traverse children
                    if "nodes" in node and node["nodes"]:
                        traverse_nodes(node["nodes"], hierarchy, depth + 1)

            traverse_nodes(tree["structure"])
        else:
            # Fallback: chunk by paragraphs if no PageIndex
            with open(md_path, 'r', encoding='utf-8') as f:
                content = f.read()

            paragraphs = content.split('\n\n')
            for i, para in enumerate(paragraphs):
                para = para.strip()
                if len(para) > 100:
                    chunks.append({
                        "text": para,
                        "title": f"Paragraph {i+1}",
                        "hierarchy": f"Paragraph {i+1}",
                        "depth": 0,
                        "line_num": 0
                    })

        return chunks

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

        logger.info("Indexes created successfully")

    def clear_collection(self):
        """Clear existing embeddings"""
        count = self.collection.count_documents({})
        if count > 0:
            logger.info(f"Clearing {count} existing documents...")
            self.collection.delete_many({})

    def build_all(self):
        """Build embeddings for all documents"""
        # Clear existing data
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
