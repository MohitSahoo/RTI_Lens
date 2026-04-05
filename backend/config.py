"""
FastAPI Backend Configuration
"""
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://mohitsahoo@localhost:5432/rtilens")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Rate limiting
RATE_LIMIT = "60/minute"

# Session settings
SESSION_TIMEOUT_SECONDS = 3600  # 1 hour
MAX_QA_CALLS_PER_SESSION = 3

# Model settings
MODEL_PATH = "data/model.pkl"
MODEL_CARD_PATH = "data/model_card.json"
BM25_INDEX_PATH = "data/bm25_pageindex.pkl"

# Gemini settings
GEMINI_MODEL = "gemini-flash-lite-latest"  # Free tier lite model
