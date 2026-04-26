"""
Analytics API Endpoints - ORM Version
Migrated from raw SQL to SQLAlchemy ORM
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, case as sql_case, Numeric
from typing import List, Optional
from datetime import datetime
import logging
from pathlib import Path
from backend.database import get_db
from backend.models import Ministry, MinistryStats, SectionStats, Case
from backend.schemas import (
    DenialRateResponse,
    SectionHeatmapResponse,
    OverrideTrendResponse,
    MinistryOrderResponse,
    GraphResponse,
    GraphNode,
    GraphEdge
)
from backend.utils.pickle_security import load_pickle_with_verification, PickleIntegrityError

router = APIRouter(prefix="/api/analytics", tags=["analytics"])
logger = logging.getLogger(__name__)


@router.get("/denial-rates", response_model=List[DenialRateResponse])
async def get_denial_rates(
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    ministry_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get denial rates by ministry with optional filters"""

    # Base query
    query = db.query(
        Ministry.id.label('ministry_id'),
        Ministry.name.label('ministry'),
        MinistryStats.total_orders,
        MinistryStats.denied_count,
        MinistryStats.allowed_count,
        MinistryStats.denial_rate,
        MinistryStats.override_rate
    ).join(
        MinistryStats, Ministry.id == MinistryStats.ministry_id
    )

    # Apply filters if provided
    if year_from or year_to or ministry_id:
        query = query.join(Case, Case.ministry_id == Ministry.id)

        if year_from:
            query = query.filter(extract('year', Case.order_date) >= year_from)

        if year_to:
            query = query.filter(extract('year', Case.order_date) <= year_to)

        if ministry_id:
            query = query.filter(Ministry.id == ministry_id)

        # Group by to avoid duplicates when joining with cases
        query = query.group_by(
            Ministry.id,
            Ministry.name,
            MinistryStats.total_orders,
            MinistryStats.denied_count,
            MinistryStats.allowed_count,
            MinistryStats.denial_rate,
            MinistryStats.override_rate
        )

    # Order by denial rate
    query = query.order_by(MinistryStats.denial_rate.desc())

    results = query.all()

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
        for row in results
    ]


@router.get("/section-heatmap", response_model=List[SectionHeatmapResponse])
async def get_section_heatmap(db: Session = Depends(get_db)):
    """Get section misuse rates by ministry"""

    results = db.query(
        SectionStats.section_cited,
        Ministry.name.label('ministry'),
        SectionStats.total_citations,
        SectionStats.overturned_count,
        SectionStats.misuse_rate
    ).join(
        Ministry, Ministry.id == SectionStats.ministry_id
    ).order_by(
        SectionStats.misuse_rate.desc()
    ).limit(50).all()

    return [
        SectionHeatmapResponse(
            section_cited=row.section_cited,
            ministry=row.ministry,
            total_citations=row.total_citations,
            overturned_count=row.overturned_count,
            misuse_rate=row.misuse_rate
        )
        for row in results
    ]


@router.get("/override-trends", response_model=List[OverrideTrendResponse])
async def get_override_trend(db: Session = Depends(get_db)):
    """Get appeal override trend over time"""

    # Aggregate by month
    results = db.query(
        func.date_trunc('month', Case.order_date).label('month'),
        func.sum(
            sql_case((Case.appeal_outcome == 'allowed', 1), else_=0)
        ).label('allowed_count'),
        func.sum(
            sql_case((Case.appeal_outcome == 'denied', 1), else_=0)
        ).label('denied_count'),
        func.round(
            func.sum(sql_case((Case.appeal_outcome == 'allowed', 1), else_=0)).cast(Numeric) /
            func.nullif(
                func.sum(
                    sql_case(
                        (Case.appeal_outcome.in_(['allowed', 'denied']), 1),
                        else_=0
                    )
                ), 0
            ),
            4
        ).label('override_rate')
    ).filter(
        Case.order_date.isnot(None),
        Case.appeal_outcome.in_(['allowed', 'denied'])
    ).group_by(
        func.date_trunc('month', Case.order_date)
    ).order_by(
        func.date_trunc('month', Case.order_date).desc()
    ).limit(24).all()

    return [
        OverrideTrendResponse(
            date=row.month.strftime('%Y-%m') if row.month else '',
            allowed_count=row.allowed_count or 0,
            denied_count=row.denied_count or 0,
            override_rate=float(row.override_rate) if row.override_rate else 0.0
        )
        for row in results
    ]


@router.get("/ministry/{ministry_id}/orders", response_model=List[MinistryOrderResponse])
async def get_ministry_orders(
    ministry_id: int,
    offset: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all orders for a specific ministry with pagination"""

    # Validate parameters
    if limit > 500:
        raise HTTPException(status_code=400, detail="Limit cannot exceed 500")
    if offset < 0:
        raise HTTPException(status_code=400, detail="Offset cannot be negative")

    # Query cases
    results = db.query(
        Case.order_number,
        Case.order_url,
        Case.section_cited,
        Case.appeal_outcome,
        Case.appeal_level,
        Case.order_date
    ).filter(
        Case.ministry_id == ministry_id
    ).order_by(
        Case.order_date.desc().nullslast()
    ).offset(offset).limit(limit).all()

    if not results and offset == 0:
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
        for row in results
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
        # Load pickle with integrity verification
        hash_file = Path(str(graph_path) + '.sha256')
        try:
            G = load_pickle_with_verification(
                graph_path,
                hash_file=hash_file if hash_file.exists() else None
            )
            logger.info("Knowledge graph loaded successfully with integrity verification")
        except PickleIntegrityError as e:
            logger.error(f"Knowledge graph integrity check failed: {e}")
            raise HTTPException(
                status_code=500,
                detail="Knowledge graph file integrity check failed. Please regenerate the graph."
            )

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

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading knowledge graph: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error loading knowledge graph: {str(e)}")
