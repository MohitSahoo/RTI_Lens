"""
Analytics API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional, Optional
import pickle
from pathlib import Path
from backend.database import get_db
from backend.schemas import (
    DenialRateResponse,
    SectionHeatmapResponse,
    OverrideTrendResponse,
    MinistryOrderResponse,
    GraphResponse,
    GraphNode,
    GraphEdge
)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

@router.get("/denial-rates", response_model=List[DenialRateResponse])
async def get_denial_rates(
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    ministry_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get denial rates by ministry with optional filters"""

    # Build WHERE clause based on filters
    where_clauses = []
    params = {}

    if year_from:
        where_clauses.append("EXTRACT(YEAR FROM c.order_date) >= :year_from")
        params["year_from"] = year_from

    if year_to:
        where_clauses.append("EXTRACT(YEAR FROM c.order_date) <= :year_to")
        params["year_to"] = year_to

    if ministry_id:
        where_clauses.append("ms.ministry_id = :ministry_id")
        params["ministry_id"] = ministry_id

    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    query = text(f"""
        SELECT
            m.id AS ministry_id,
            m.name AS ministry,
            ms.total_orders,
            ms.denied_count,
            ms.allowed_count,
            ms.denial_rate,
            ms.override_rate
        FROM ministry_stats ms
        JOIN ministries m ON m.id = ms.ministry_id
        LEFT JOIN cases c ON c.ministry_id = ms.ministry_id
        {where_sql}
        GROUP BY m.id, m.name, ms.total_orders, ms.denied_count, ms.allowed_count, ms.denial_rate, ms.override_rate
        ORDER BY ms.denial_rate DESC
    """)

    result = db.execute(query, params).fetchall()

    return [
        DenialRateResponse(
            ministry_id=row.ministry_id,
            ministry=row.ministry,
            total_orders=row.total_orders,
            denied_count=row.denied_count,
            allowed_count=row.allowed_count,
            denial_rate=row.denial_rate,
            override_rate=row.override_rate
        )
        for row in result
    ]

@router.get("/section-heatmap", response_model=List[SectionHeatmapResponse])
async def get_section_heatmap(db: Session = Depends(get_db)):
    """Get section misuse rates by ministry"""
    query = text("""
        SELECT
            ss.section_cited,
            m.name AS ministry,
            ss.total_citations,
            ss.overturned_count,
            ss.misuse_rate
        FROM section_stats ss
        JOIN ministries m ON m.id = ss.ministry_id
        ORDER BY ss.misuse_rate DESC
        LIMIT 50
    """)

    result = db.execute(query).fetchall()

    return [
        SectionHeatmapResponse(
            section_cited=row.section_cited,
            ministry=row.ministry,
            total_citations=row.total_citations,
            overturned_count=row.overturned_count,
            misuse_rate=row.misuse_rate
        )
        for row in result
    ]

@router.get("/override-trend", response_model=List[OverrideTrendResponse])
async def get_override_trend(db: Session = Depends(get_db)):
    """Get appeal override trend over time"""
    query = text("""
        SELECT
            DATE_TRUNC('month', order_date) AS month,
            SUM(CASE WHEN appeal_outcome = 'allowed' THEN 1 ELSE 0 END) AS allowed_count,
            SUM(CASE WHEN appeal_outcome = 'denied' THEN 1 ELSE 0 END) AS denied_count,
            ROUND(
                SUM(CASE WHEN appeal_outcome = 'allowed' THEN 1 ELSE 0 END)::NUMERIC /
                NULLIF(SUM(CASE WHEN appeal_outcome IN ('allowed', 'denied') THEN 1 ELSE 0 END), 0),
                4
            ) AS override_rate
        FROM cases
        WHERE order_date IS NOT NULL
          AND appeal_outcome IN ('allowed', 'denied')
        GROUP BY DATE_TRUNC('month', order_date)
        ORDER BY month DESC
        LIMIT 24
    """)

    result = db.execute(query).fetchall()

    return [
        OverrideTrendResponse(
            date=row.month.strftime('%Y-%m') if row.month else '',
            allowed_count=row.allowed_count or 0,
            denied_count=row.denied_count or 0,
            override_rate=float(row.override_rate) if row.override_rate else 0.0
        )
        for row in result
    ]

@router.get("/ministry/{ministry_id}/orders", response_model=List[MinistryOrderResponse])
async def get_ministry_orders(
    ministry_id: int,
    offset: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all orders for a specific ministry with pagination"""

    # Validate limit
    if limit > 500:
        raise HTTPException(status_code=400, detail="Limit cannot exceed 500")
    if offset < 0:
        raise HTTPException(status_code=400, detail="Offset cannot be negative")

    # Use f-string for LIMIT/OFFSET since SQLAlchemy text() doesn't support them as parameters
    query = text(f"""
        SELECT
            order_number,
            order_url,
            section_cited,
            appeal_outcome,
            appeal_level,
            order_date
        FROM cases
        WHERE ministry_id = :ministry_id
        ORDER BY order_date DESC NULLS LAST
        LIMIT {limit} OFFSET {offset}
    """)

    result = db.execute(query, {"ministry_id": ministry_id}).fetchall()

    if not result and offset == 0:
        raise HTTPException(status_code=404, detail="Ministry not found or no orders available")

    return [
        MinistryOrderResponse(
            order_number=row.order_number,
            order_url=row.order_url,
            section_cited=row.section_cited,
            appeal_outcome=row.appeal_outcome,
            appeal_level=row.appeal_level,
            order_date=row.order_date
        )
        for row in result
    ]

@router.get("/graph", response_model=GraphResponse)
async def get_knowledge_graph():
    """Get the knowledge graph for visualization"""
    graph_path = Path(__file__).parent.parent.parent / "data" / "knowledge_graph.pkl"

    if not graph_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Knowledge graph not found. Run scripts/build_knowledge_graph.py first."
        )

    try:
        with open(graph_path, 'rb') as f:
            G = pickle.load(f)

        # Convert NetworkX graph to API response format
        nodes = [
            GraphNode(id=node, type=data.get('node_type', 'unknown'))
            for node, data in G.nodes(data=True)
        ]

        edges = [
            GraphEdge(
                source=source,
                target=target,
                weight=data.get('weight', 0.0),
                edge_type=data.get('edge_type', 'unknown'),
                count=data.get('count')
            )
            for source, target, data in G.edges(data=True)
        ]

        return GraphResponse(nodes=nodes, edges=edges)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading knowledge graph: {str(e)}")
