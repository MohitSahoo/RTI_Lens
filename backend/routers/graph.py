"""
Knowledge Graph API Endpoint
Returns the RTI case knowledge graph showing relationships between ministries, sections, and outcomes
"""
from fastapi import APIRouter, HTTPException
from pathlib import Path
import json

router = APIRouter(prefix="/api", tags=["graph"])

GRAPH_PATH = Path(__file__).parent.parent.parent / "data" / "knowledge_graph.json"

@router.get("/graph")
async def get_knowledge_graph():
    """
    Get the knowledge graph showing relationships between:
    - Ministries (which ministries cite which sections)
    - Sections (which sections lead to which outcomes)
    - Outcomes (allowed, denied, partially_allowed)

    Returns:
        nodes: List of graph nodes with id, name, and type
        edges: List of graph edges with source, target, type, and weight
        metadata: Graph statistics
    """
    if not GRAPH_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="Knowledge graph not found. Run scripts/build_knowledge_graph.py first."
        )

    try:
        with open(GRAPH_PATH, 'r') as f:
            graph_data = json.load(f)

        return graph_data

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error loading knowledge graph: {str(e)}"
        )
