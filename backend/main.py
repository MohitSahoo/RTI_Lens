"""
FastAPI Application - ORM Version with GraphQL
Uses SQLAlchemy ORM models and GraphQL API
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter
from backend.config import API_HOST, API_PORT
from backend.routers import qa, draft, analytics, predict, dashboard
from backend.routers.graph import router as graph_router
from backend.gql.queries import schema

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="RTI-Lens API",
    description="AI-powered analytics for RTI Act rulings with GraphQL",
    version="2.0.0"
)

# CORS middleware - restrict to known origins
# For production, update with actual frontend domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",  # Streamlit dev server
        "http://127.0.0.1:8501",  # Streamlit alternative
        # Add production frontend URL here when deployed
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Include REST routers
app.include_router(analytics.router)
app.include_router(predict.router)
app.include_router(graph_router)
app.include_router(dashboard.router)
app.include_router(qa.router)
app.include_router(draft.router)

# Include GraphQL router
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")

@app.get("/")
async def root():
    return {
        "message": "RTI-Lens API",
        "version": "2.0.0",
        "docs": "/docs",
        "graphql": "/graphql",
        "endpoints": {
            "rest": {
                "analytics": "/api/analytics/*",
                "prediction": "/api/predict",
                "qa": "/api/qa",
                "draft": "/api/draft",
                "graph": "/api/graph",
                "dashboard": "/api/dashboard/*"
            },
            "graphql": {
                "endpoint": "/graphql",
                "playground": "/graphql (interactive)"
            }
        }
    }

@app.get("/health")
async def health_check():
    """System health check"""
    from backend.utils.bm25_loader import BM25Loader
    from backend.utils.pageindex_loader import PageIndexLoader

    try:
        # Check BM25 index
        bm25_loader = BM25Loader()
        bm25_status = "loaded" if bm25_loader.get_bm25() else "not loaded"

        # Check PageIndex
        pageindex_loader = PageIndexLoader()
        pageindex_status = f"loaded ({len(pageindex_loader.order_number_to_hash)} mappings)"

        # Check database connection
        from backend.database import SessionLocal
        db = SessionLocal()
        try:
            from backend.models import Case
            case_count = db.query(Case).count()
            db_status = f"connected ({case_count} cases)"
        finally:
            db.close()

        return {
            "status": "healthy",
            "database": db_status,
            "bm25_index": bm25_status,
            "pageindex": pageindex_status,
            "orm_mode": True
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "orm_mode": True
        }

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting RTI-Lens API (ORM mode) on {API_HOST}:{API_PORT}")
    uvicorn.run(app, host=API_HOST, port=API_PORT)
