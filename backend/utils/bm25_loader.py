"""
BM25 Loader with Metadata Filtering Support

Loads BM25 index and provides search with optional metadata filtering.
"""
import pickle
import logging
from pathlib import Path
from typing import List, Dict, Optional
import re

from backend.utils.pickle_security import load_pickle_with_verification, PickleIntegrityError

logger = logging.getLogger(__name__)

BM25_INDEX_PATH = Path("data/bm25_pageindex.pkl")


class BM25Loader:
    """Load and search BM25 index with metadata filtering"""

    _bm25 = None
    _index = None

    @classmethod
    def _load_index(cls):
        """Load BM25 index from disk"""
        path = BM25_INDEX_PATH
        if not path.exists():
            raise FileNotFoundError(f"BM25 index not found at {path}")

        hash_file = Path(str(path) + '.sha256')
        try:
            data = load_pickle_with_verification(
                path,
                hash_file=hash_file if hash_file.exists() else None
            )
            cls._bm25 = data["bm25"]
            cls._index = data["index"]
            logger.info("BM25 index loaded successfully with integrity verification")
        except PickleIntegrityError as e:
            logger.error(f"BM25 index integrity check failed: {e}")
            raise FileNotFoundError(
                "BM25 index file integrity check failed. Please regenerate the index with scripts/build_bm25.py"
            )

    @classmethod
    def get_bm25(cls):
        """Get BM25 instance"""
        if cls._bm25 is None:
            cls._load_index()
        return cls._bm25

    @classmethod
    def get_index(cls):
        """Get page index"""
        if cls._index is None:
            cls._load_index()
        return cls._index

    @classmethod
    def _matches_filter(cls, paragraph: Dict, metadata_filter: Dict) -> bool:
        """
        Check if paragraph matches metadata filter
        
        Args:
            paragraph: Paragraph dict with metadata
            metadata_filter: Filter dict with ministry, section_cited, order_date
            
        Returns:
            True if paragraph matches all filter criteria
        """
        if not metadata_filter:
            return True
        
        # Ministry filter
        if "ministry" in metadata_filter:
            ministry_filter = metadata_filter["ministry"]
            para_ministry = paragraph.get("ministry", "").lower()
            
            if isinstance(ministry_filter, str):
                if ministry_filter.lower() not in para_ministry:
                    return False
            elif isinstance(ministry_filter, dict):
                # Handle regex patterns from EntityExtractor
                if "$regex" in ministry_filter:
                    pattern = ministry_filter["$regex"]
                    options = ministry_filter.get("$options", "")
                    flags = re.IGNORECASE if "i" in options else 0
                    if not re.search(pattern, para_ministry, flags):
                        return False
        
        # Section filter (if available in BM25 index)
        if "section_cited" in metadata_filter and "section_cited" in paragraph:
            section_filter = metadata_filter["section_cited"]
            para_section = paragraph.get("section_cited", "")
            
            if isinstance(section_filter, dict) and "$regex" in section_filter:
                pattern = section_filter["$regex"]
                if not re.search(pattern, para_section):
                    return False
        
        # Order date filter
        if "order_date" in metadata_filter and "order_date" in paragraph:
            date_filter = metadata_filter["order_date"]
            para_date = paragraph.get("order_date")
            
            if isinstance(date_filter, dict):
                if "$gte" in date_filter and para_date and para_date < date_filter["$gte"]:
                    return False
                if "$lte" in date_filter and para_date and para_date > date_filter["$lte"]:
                    return False
        
        # Handle $and operator
        if "$and" in metadata_filter:
            for sub_filter in metadata_filter["$and"]:
                if not cls._matches_filter(paragraph, sub_filter):
                    return False
        
        # Handle $or operator
        if "$or" in metadata_filter:
            any_match = False
            for sub_filter in metadata_filter["$or"]:
                if cls._matches_filter(paragraph, sub_filter):
                    any_match = True
                    break
            if not any_match:
                return False
        
        return True

    @classmethod
    def search(cls, query: str, top_k: int = 5, metadata_filter: Optional[Dict] = None):
        """
        Search BM25 index and return top-k results
        
        Args:
            query: Search query
            top_k: Number of results to return
            metadata_filter: Optional metadata filter dict
            
        Returns:
            List of results with scores and paragraphs
        """
        import re
        from nltk.corpus import stopwords

        STOPWORDS = set(stopwords.words('english'))

        def tokenize(text: str):
            """
            Tokenize text while preserving section numbers like 8(1)(a), 8(1)a, 2(f), etc.
            """
            import re
            # Normalize to lowercase
            text = text.lower()
            
            # Pattern for RTI section numbers and other alphanumeric codes
            # This matches: 8(1)(a), 2(f), 4(1)(b), 8(1)a, etc.
            section_pattern = re.compile(r'\b\d+\(?[\w\d]*\)?(?:\(?[\w\d]*\)?)*\b')
            
            # Extract section numbers first
            sections = section_pattern.findall(text)
            
            # Remove symbols except those used in section numbers, then split
            clean_text = re.sub(r'[^a-z0-9\(\)\[\]]', ' ', text)
            tokens = clean_text.split()
            
            result = []
            STOPWORDS = set(stopwords.words('english'))

            # Process tokens
            for t in tokens:
                # If it's in our pre-extracted sections, keep it
                if t in sections or section_pattern.match(t):
                    result.append(t)
                    continue
                
                # Strip parentheses for normal word check
                t_word = t.strip('()[]')
                if len(t_word) > 1 and t_word.isalnum() and t_word not in STOPWORDS:
                    result.append(t_word)
                elif t_word.isalpha() and t_word not in STOPWORDS:
                    result.append(t_word)

            return list(set(result)) # Unique tokens

        bm25 = cls.get_bm25()
        index = cls.get_index()

        query_tokens = tokenize(query)
        scores = bm25.get_scores(query_tokens)

        # Get top-k indices (fetch more if filtering to ensure we have enough results)
        fetch_count = top_k * 3 if metadata_filter else top_k
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:fetch_count]

        results = []
        for idx in top_indices:
            paragraph = index[idx]
            
            # Apply metadata filter
            if metadata_filter and not cls._matches_filter(paragraph, metadata_filter):
                continue
            
            results.append({
                "score": float(scores[idx]),
                "paragraph": paragraph
            })
            
            # Stop when we have enough results
            if len(results) >= top_k:
                break

        if metadata_filter and results:
            logger.info(f"BM25 search with filter returned {len(results)} results (fetched {fetch_count} candidates)")

        return results
