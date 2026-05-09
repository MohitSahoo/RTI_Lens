"""
FastAPI Backend Configuration
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://mohitsahoo@localhost:5432/rtilens")

# API Keys with validation
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
BACKBOARD_API_KEY = os.getenv("BACKBOARD_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

# Validate API key formats at startup
if OPENAI_API_KEY and OPENAI_API_KEY != "your_openai_api_key_here":
    if not OPENAI_API_KEY.startswith("sk-"):
        raise ValueError(
            "Invalid OPENAI_API_KEY format. Expected key starting with 'sk-'. "
            "Get a valid key from https://platform.openai.com/api-keys"
        )

# Server settings
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8001"))

# Rate limiting
RATE_LIMIT = "60/minute"

# Session settings
SESSION_TIMEOUT_SECONDS = 3600  # 1 hour
MAX_QA_CALLS_PER_SESSION = 20

# Model settings
MODEL_PATH = "data/model.pkl"
MODEL_CARD_PATH = "data/model_card.json"
BM25_INDEX_PATH = "data/bm25_pageindex.pkl"

# OpenAI settings
OPENAI_MODEL = "gpt-4o-mini"  # Cheap and fast

# Groq settings
GROQ_MODEL = "llama-3.1-8b-instant"  # Faster and higher rate limits

# MongoDB Vector Store
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
MONGODB_DB = os.getenv("MONGODB_DB", "rtilens_vectors")
MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION", "document_embeddings")

# Embedding Model
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
EMBEDDING_DIMENSION = 384  # Dimension for all-MiniLM-L6-v2

# Hybrid Search Weights
BM25_WEIGHT = float(os.getenv("BM25_WEIGHT", "0.4"))
SEMANTIC_WEIGHT = float(os.getenv("SEMANTIC_WEIGHT", "0.6"))

# Backboard Workflow Settings
BACKBOARD_ENABLED = os.getenv("BACKBOARD_ENABLED", "true").lower() == "true"

# Solana Settings
SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.devnet.solana.com")
SOLANA_PRIVATE_KEY = os.getenv("SOLANA_PRIVATE_KEY")
