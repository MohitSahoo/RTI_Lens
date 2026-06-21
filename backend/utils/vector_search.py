"""
Vector Search Loader for semantic similarity search using MongoDB
"""
import logging
import re
import numpy as np
from typing import List, Dict, Optional
from pymongo import MongoClient
from backend.config import (
    MONGODB_URI,
    MONGODB_DB,
    MONGODB_COLLECTION,
    MONGODB_VECTOR_INDEX,
    MONGODB_VECTOR_CANDIDATES,
    EMBEDDING_MODEL
)

logger = logging.getLogger(__name__)


class VectorSearchLoader:
    """Singleton loader for semantic vector search"""

    _instance = None
    _model = None
    _client = None
    _collection = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VectorSearchLoader, cls).__new__(cls)
            cls._load_model()
            cls._connect_db()
        return cls._instance

    @classmethod
    def _load_model(cls):
        """Load sentence-transformer model"""
        try:
            from sentence_transformers import SentenceTransformer
            cls._model = SentenceTransformer(EMBEDDING_MODEL)
            logger.info(f"Loaded embedding model: {EMBEDDING_MODEL}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise

    @classmethod
    def _connect_db(cls):
        """Connect to MongoDB"""
        try:
            cls._client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=2000)
            db = cls._client[MONGODB_DB]
            cls._collection = db[MONGODB_COLLECTION]

            # Check if collection exists and has documents
            doc_count = cls._collection.count_documents({})
            logger.info(f"Connected to MongoDB. Collection has {doc_count} documents")

            if doc_count == 0:
                logger.warning(
                    "Vector collection is empty. Run scripts/build_embeddings.py to populate it."
                )
        except Exception as e:
            logger.warning(f"Failed to connect to MongoDB: {e}. Vector search will be disabled.")
            cls._collection = None
            cls._client = None

    @classmethod
    def get_model(cls):
        """Get embedding model instance"""
        if cls._model is None:
            cls._load_model()
        return cls._model

    @classmethod
    def get_collection(cls):
        """Get MongoDB collection"""
        if cls._collection is None:
            cls._connect_db()
        return cls._collection

    @classmethod
    def embed_query(cls, query: str) -> np.ndarray:
        """Generate embedding for a query string"""
        model = cls.get_model()
        embedding = model.encode(query, convert_to_numpy=True)
        return embedding

    @classmethod
    def cosine_similarity(cls, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

    @classmethod
    def search(cls, query: str, top_k: int = 5, filter_dict: Optional[Dict] = None) -> List[Dict]:
        """
        Semantic search using MongoDB vector search when available.

        Args:
            query: Search query string
            top_k: Number of results to return
            filter_dict: Optional MongoDB filter (e.g., {"ministry": "Ministry of Finance"})

        Returns:
            List of results with score and document metadata
        """
        collection = cls.get_collection()

        # Check if collection is available
        if collection is None:
            logger.warning("Vector search is disabled (no MongoDB connection).")
            return []

        # Check if collection is empty
        try:
            if collection.count_documents({}, limit=1) == 0:
                logger.warning("Vector collection is empty. Returning empty results.")
                return []
        except Exception as e:
            logger.warning(f"Error checking collection count: {e}")
            return []

        # Generate query embedding
        query_embedding = cls.embed_query(query).tolist()

        try:
            pipeline = [
                {
                    "$vectorSearch": {
                        "index": MONGODB_VECTOR_INDEX,
                        "path": "embedding",
                        "queryVector": query_embedding,
                        "numCandidates": max(MONGODB_VECTOR_CANDIDATES, top_k * 10),
                        "limit": top_k
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "order_number": 1,
                        "order_hash": 1,
                        "ministry": 1,
                        "order_date": 1,
                        "section_cited": 1,
                        "appeal_outcome": 1,
                        "appeal_level": 1,
                        "text": 1,
                        "chunk_index": 1,
                        "hierarchy": 1,
                        "title": 1,
                        "score": {"$meta": "vectorSearchScore"}
                    }
                }
            ]

            if filter_dict:
                pipeline[0]["$vectorSearch"]["filter"] = filter_dict

            results = []
            for doc in collection.aggregate(pipeline):
                results.append({
                    "score": float(doc.get("score", 0.0)),
                    "paragraph": {
                        "order_number": doc["order_number"],
                        "order_hash": doc["order_hash"],
                        "ministry": doc.get("ministry", "Unknown"),
                        "order_date": doc.get("order_date"),
                        "section_cited": doc.get("section_cited"),
                        "appeal_outcome": doc.get("appeal_outcome"),
                        "appeal_level": doc.get("appeal_level"),
                        "text": doc["text"],
                        "chunk_index": doc.get("chunk_index", 0),
                        "hierarchy": doc.get("hierarchy", ""),
                        "title": doc.get("title", "")
                    }
                })

            return results
        except Exception as e:
            logger.warning(
                "MongoDB vector search query failed for index '%s': %s. Falling back to in-memory similarity scan.",
                MONGODB_VECTOR_INDEX,
                e
            )

        # Legacy fallback for deployments without MongoDB vector search support
        mongo_filter = filter_dict if filter_dict else {}
        cursor = collection.find(mongo_filter)

        results = []
        query_embedding = np.array(query_embedding)
        for doc in cursor:
            doc_embedding = np.array(doc["embedding"])
            similarity = cls.cosine_similarity(query_embedding, doc_embedding)

            results.append({
                "score": similarity,
                "paragraph": {
                    "order_number": doc["order_number"],
                    "order_hash": doc["order_hash"],
                    "ministry": doc.get("ministry", "Unknown"),
                    "order_date": doc.get("order_date"),
                    "section_cited": doc.get("section_cited"),
                    "appeal_outcome": doc.get("appeal_outcome"),
                    "appeal_level": doc.get("appeal_level"),
                    "text": doc["text"],
                    "chunk_index": doc.get("chunk_index", 0),
                    "hierarchy": doc.get("hierarchy", ""),
                    "title": doc.get("title", "")
                }
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    @classmethod
    def hybrid_search(
        cls,
        query: str,
        bm25_results: List[Dict],
        top_k: int = 5,
        bm25_weight: float = 0.4,
        semantic_weight: float = 0.6,
        filter_dict: Optional[Dict] = None,
        enable_structural_boost: bool = True
    ) -> List[Dict]:
        """
        Combine BM25 and semantic search results with weighted scoring

        Issue #20: Added structural verification boosting for better relevance

        Args:
            query: Search query
            bm25_results: Results from BM25 search
            top_k: Number of final results
            bm25_weight: Weight for BM25 scores (0-1)
            semantic_weight: Weight for semantic scores (0-1)
            filter_dict: Optional MongoDB filter for metadata-aware retrieval
            enable_structural_boost: Apply structural verification boosting

        Returns:
            Merged and re-ranked results with structural boosting
        """
        # Get semantic results with optional filtering
        semantic_results = cls.search(query, top_k=top_k * 2, filter_dict=filter_dict)

        if not semantic_results:
            # Fallback to BM25 only
            logger.warning("No semantic results found. Using BM25 only.")
            return bm25_results[:top_k]

        # Normalize scores to [0, 1] range
        def normalize_scores(results: List[Dict], score_key: str = "score") -> List[Dict]:
            if not results:
                return results

            scores = [r[score_key] for r in results]
            min_score = min(scores)
            max_score = max(scores)

            if max_score == min_score:
                for r in results:
                    r[f"{score_key}_normalized"] = 1.0
            else:
                for r in results:
                    r[f"{score_key}_normalized"] = (r[score_key] - min_score) / (max_score - min_score)

            return results

        bm25_results = normalize_scores(bm25_results)
        semantic_results = normalize_scores(semantic_results)

        # Build combined results map
        combined = {}

        # Add BM25 results
        for result in bm25_results:
            key = result["paragraph"]["order_number"]
            combined[key] = {
                "paragraph": result["paragraph"],
                "bm25_score": result["score_normalized"],
                "semantic_score": 0.0
            }

        # Add/merge semantic results
        for result in semantic_results:
            key = result["paragraph"]["order_number"]
            if key in combined:
                combined[key]["semantic_score"] = result["score_normalized"]
            else:
                combined[key] = {
                    "paragraph": result["paragraph"],
                    "bm25_score": 0.0,
                    "semantic_score": result["score_normalized"]
                }

        # Calculate hybrid scores with optional structural boosting
        hybrid_results = []
        for key, data in combined.items():
            # Base hybrid score
            hybrid_score = (
                bm25_weight * data["bm25_score"] +
                semantic_weight * data["semantic_score"]
            )

            # Apply structural verification boosting (Issue #20)
            structural_boost = 0.0
            if enable_structural_boost:
                structural_boost = cls._calculate_structural_boost(
                    query,
                    data["paragraph"]
                )
                hybrid_score = hybrid_score * (1.0 + structural_boost)

            hybrid_results.append({
                "score": hybrid_score,
                "bm25_score": data["bm25_score"],
                "semantic_score": data["semantic_score"],
                "structural_boost": structural_boost,
                "paragraph": data["paragraph"]
            })

        # Sort by hybrid score
        hybrid_results.sort(key=lambda x: x["score"], reverse=True)

        return hybrid_results[:top_k]

    @classmethod
    def _calculate_structural_boost(cls, query: str, paragraph: Dict) -> float:
        """
        Calculate structural verification boost based on metadata alignment

        Issue #20: Boost scores when structural features match query

        Boosts applied for:
        - Section citation match (+0.15)
        - Ministry match (+0.10)
        - Date range overlap (+0.05)

        Returns:
            Boost multiplier (0.0 to 0.30)
        """
        boost = 0.0
        query_lower = query.lower()

        # Section citation match
        section_cited = paragraph.get("section_cited", "")
        if section_cited:
            # Extract sections from query
            section_pattern = r'\b(\d+\(\d+\)\([a-z]\))\b'
            query_sections = re.findall(section_pattern, query_lower)

            if query_sections:
                for query_section in query_sections:
                    if query_section in section_cited.lower():
                        boost += 0.15
                        logger.debug(f"Section match boost: {query_section}")
                        break

        # Ministry match
        ministry = paragraph.get("ministry", "")
        if ministry:
            # Check if ministry mentioned in query
            ministry_keywords = ministry.lower().split()
            if any(kw in query_lower for kw in ministry_keywords if len(kw) > 3):
                boost += 0.10
                logger.debug(f"Ministry match boost: {ministry}")

        # Date range overlap (basic check)
        order_date = paragraph.get("order_date", "")
        if order_date:
            # Extract years from query
            year_pattern = r'\b(20\d{2}|19\d{2})\b'
            query_years = re.findall(year_pattern, query)

            if query_years and any(year in str(order_date) for year in query_years):
                boost += 0.05
                logger.debug(f"Date match boost: {order_date}")

        return min(boost, 0.30)  # Cap at 30% boost

    @classmethod
    def close(cls):
        """Close MongoDB connection"""
        if cls._client:
            cls._client.close()
            logger.info("MongoDB connection closed")
