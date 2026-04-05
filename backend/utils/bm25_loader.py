"""
BM25 Index Singleton Loader
"""
import pickle
from pathlib import Path
from backend.config import BM25_INDEX_PATH

class BM25Loader:
    _instance = None
    _bm25 = None
    _index = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BM25Loader, cls).__new__(cls)
            cls._load_index()
        return cls._instance

    @classmethod
    def _load_index(cls):
        """Load BM25 index from pickle file"""
        path = Path(BM25_INDEX_PATH)
        if not path.exists():
            raise FileNotFoundError(f"BM25 index not found at {BM25_INDEX_PATH}")

        with open(path, "rb") as f:
            data = pickle.load(f)
            cls._bm25 = data["bm25"]
            cls._index = data["index"]

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
    def search(cls, query: str, top_k: int = 5):
        """Search BM25 index and return top-k results"""
        from nltk.corpus import stopwords

        STOPWORDS = set(stopwords.words('english'))

        def tokenize(text: str):
            tokens = text.lower().split()
            return [t for t in tokens if t.isalpha() and t not in STOPWORDS]

        bm25 = cls.get_bm25()
        index = cls.get_index()

        query_tokens = tokenize(query)
        scores = bm25.get_scores(query_tokens)

        # Get top-k indices
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

        results = []
        for idx in top_indices:
            results.append({
                "score": float(scores[idx]),
                "paragraph": index[idx]
            })

        return results
