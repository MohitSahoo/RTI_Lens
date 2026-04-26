"""
FastAPI Backend Configuration
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://mohitsahoo@localhost:5432/rtilens")

# API Keys with validation
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Validate API key formats at startup
if GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here":
    if not GEMINI_API_KEY.startswith("AI"):
        raise ValueError(
            "Invalid GEMINI_API_KEY format. Expected key starting with 'AI'. "
            "Get a valid key from https://aistudio.google.com/apikey"
        )

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

# Gemini settings
GEMINI_MODEL = "gemini-flash-lite-latest"  # Free tier lite model
