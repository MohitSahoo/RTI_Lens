"""
RTI-Lens FastAPI Backend
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager
import time
from collections import defaultdict

from backend.routers import analytics, qa, draft, predict, graph
from backend.config import RATE_LIMIT

# Session call counter (in-memory, 1hr TTL)
session_calls = defaultdict(lambda: {"count": 0, "timestamp": time.time()})

def cleanup_sessions():
    """Remove expired sessions (older than 1 hour)"""
    current_time = time.time()
    expired = [
        session_id for session_id, data in session_calls.items()
        if current_time - data["timestamp"] > 3600
    ]
    for session_id in expired:
        del session_calls[session_id]

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    print("🚀 RTI-Lens API starting up...")
    print("📊 Loading BM25 index...")
    from backend.utils.bm25_loader import BM25Loader
    BM25Loader()  # Initialize singleton
    print("✅ BM25 index loaded")

    print("🤖 Loading ML model...")
    from backend.routers.predict import load_model
    load_model()
    print("✅ ML model loaded")

    yield

    # Shutdown
    print("👋 RTI-Lens API shutting down...")

# Initialize FastAPI app
app = FastAPI(
    title="RTI-Lens API",
    description="AI-powered RTI case analytics and appeal assistance",
    version="1.0.0",
    lifespan=lifespan
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session tracking middleware
@app.middleware("http")
async def track_sessions(request: Request, call_next):
    """Track API calls per session and add rate limit headers"""
    session_id = request.headers.get("X-Session-ID", get_remote_address(request))

    # Cleanup old sessions periodically
    if len(session_calls) > 1000:
        cleanup_sessions()

    # Update session counter
    session_calls[session_id]["count"] += 1
    session_calls[session_id]["timestamp"] = time.time()

    response = await call_next(request)

    # Add session tracking header
    response.headers["X-Session-Calls"] = str(session_calls[session_id]["count"])

    # Add rate limit headers (60 requests per minute)
    rate_limit_max = 60
    rate_limit_window = 60  # seconds

    # Calculate remaining based on session calls in last minute
    current_time = time.time()
    session_age = current_time - session_calls[session_id]["timestamp"]

    if session_age < rate_limit_window:
        remaining = max(0, rate_limit_max - session_calls[session_id]["count"])
        reset_time = int(session_calls[session_id]["timestamp"] + rate_limit_window)
    else:
        # Session expired, reset counter
        remaining = rate_limit_max
        reset_time = int(current_time + rate_limit_window)

    response.headers["X-RateLimit-Limit"] = str(rate_limit_max)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Reset"] = str(reset_time)

    return response

# Include routers
app.include_router(analytics.router)
app.include_router(qa.router)
app.include_router(draft.router)
app.include_router(predict.router)
app.include_router(graph.router)

# Health check endpoint
@app.get("/health")
@limiter.limit("100/minute")
async def health_check(request: Request):
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "services": {
            "database": "connected",
            "bm25": "loaded",
            "ml_model": "loaded"
        }
    }

# Root endpoint
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "RTI-Lens API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "analytics": "/api/analytics/*",
            "qa": "/api/qa",
            "draft": "/api/draft",
            "predict": "/api/predict",
            "graph": "/api/graph"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
