"""
Query Assistant API Endpoint
Provides query optimization suggestions based on precedent analysis
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List, Dict, Optional
import logging
import sys
import time

# Import service using relative path or ensuring package is in sys.path
try:
    from app.services.query_optimizer import QueryOptimizer
except ImportError:
    # Fallback if package structure is different
    import sys
    import os
    sys.path.append(os.getcwd())
    from app.services.query_optimizer import QueryOptimizer

from backend.config import MAX_QA_CALLS_PER_SESSION

router = APIRouter(prefix="/api", tags=["query-assistant"])
logger = logging.getLogger(__name__)

# Session tracking (in-memory, consistent with QA endpoint)
query_assistant_session_calls = {}

def cleanup_expired_sessions():
    """Remove sessions older than 1 hour"""
    current_time = time.time()
    expired = [
        session_id for session_id, data in query_assistant_session_calls.items()
        if current_time - data["timestamp"] > 3600
    ]
    for session_id in expired:
        del query_assistant_session_calls[session_id]

def get_session_id(request: Request) -> str:
    """Extract session ID from request headers or generate new one"""
    return request.headers.get("X-Session-ID", request.client.host if request.client else "unknown")

class QueryOptimizeRequest(BaseModel):
    query: str

class QueryOptimizeResponse(BaseModel):
    status: str
    original_query: str
    optimized_query: str
    ministry_suggestion: Dict
    section_recommendations: Dict
    relevant_precedents: List[Dict]
    issues_detected: List[Dict]
    improvements_made: List[str]
    scores: Dict
    metadata: Dict
    calls_remaining: Optional[int] = None
    session_id: Optional[str] = None

# Initialize optimizer once
_optimizer = None

def get_optimizer():
    """Lazy load optimizer"""
    global _optimizer
    if _optimizer is None:
        _optimizer = QueryOptimizer()
    return _optimizer

@router.post("/query-assistant/optimize", response_model=QueryOptimizeResponse)
async def optimize_query(http_request: Request, request: QueryOptimizeRequest):
    """
    Optimize RTI query and provide suggestions

    - Analyzes query using hybrid search (BM25 + vector)
    - Suggests relevant ministry based on precedents
    - Recommends applicable RTI sections
    - Provides query improvements
    - Returns relevant precedent cases
    - Tracks session calls (max 20 per session)
    """
    # Validate query before try-except to ensure proper HTTP status codes
    if not request.query or len(request.query.strip()) < 5:
        raise HTTPException(
            status_code=400,
            detail="Query must be at least 5 characters long"
        )

    # Session management
    cleanup_expired_sessions()
    session_id = get_session_id(http_request)

    if session_id not in query_assistant_session_calls:
        query_assistant_session_calls[session_id] = {"count": 0, "timestamp": time.time()}

    if query_assistant_session_calls[session_id]["count"] >= MAX_QA_CALLS_PER_SESSION:
        raise HTTPException(
            status_code=429,
            detail=f"Session limit reached. Maximum {MAX_QA_CALLS_PER_SESSION} calls per session."
        )

    query_assistant_session_calls[session_id]["count"] += 1
    query_assistant_session_calls[session_id]["timestamp"] = time.time()

    try:
        optimizer = get_optimizer()
        result = optimizer.optimize(request.query)

        # Add session info to response
        result["calls_remaining"] = MAX_QA_CALLS_PER_SESSION - query_assistant_session_calls[session_id]["count"]
        result["session_id"] = session_id

        return QueryOptimizeResponse(**result)

    except ValueError as e:
        logger.error(f"Validation error in query optimization: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in query optimization: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while optimizing the query. Please try again."
        )

@router.get("/query-assistant/health")
async def health_check():
    """Check if query assistant is ready"""
    try:
        optimizer = get_optimizer()
        return {
            "status": "healthy",
            "optimizer_loaded": optimizer is not None,
            "dependencies": {
                "bm25": "loaded",
                "vector_search": "loaded",
                "entity_extractor": "loaded"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }
