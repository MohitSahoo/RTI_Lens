"""
Dashboard Graph API Endpoint
Serves enhanced knowledge graph with visual metadata for frontend
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pathlib import Path
import json
from backend.database import get_db

router = APIRouter(prefix="/api", tags=["dashboard"])

DASHBOARD_GRAPH_PATH = Path(__file__).parent.parent.parent / "data" / "dashboard_graph.json"

@router.get("/dashboard/graph")
async def get_dashboard_graph():
    """
    Get enhanced knowledge graph for dashboard visualization

    Returns:
        nodes: List of nodes with visual metadata (color, size, importance)
        edges: List of edges with visual metadata (thickness, color, animation)
        metadata: Graph statistics

    Node types:
        - ministry: Government ministries (blue, sized by case count)
        - section: RTI Act sections (amber, sized by citations)
        - outcome: Appeal outcomes (green/red/amber)

    Edge types:
        - cites: Ministry → Section (gray, thickness by citation count)
        - leads_to: Section → Outcome (light gray, animated, thickness by probability)
    """
    if not DASHBOARD_GRAPH_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="Dashboard graph not found. Run scripts/build_dashboard_graph.py first."
        )

    try:
        with open(DASHBOARD_GRAPH_PATH, 'r') as f:
            graph_data = json.load(f)

        return graph_data

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error loading dashboard graph: {str(e)}"
        )


@router.get("/dashboard/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Get high-level statistics for dashboard overview
    """
    from sqlalchemy import text

    try:
        # Overall stats
        total_cases = db.execute(text("SELECT COUNT(*) FROM cases")).scalar()
        total_ministries = db.execute(text("SELECT COUNT(*) FROM ministries")).scalar()

        # Outcome distribution
        outcomes = db.execute(text("""
            SELECT
                appeal_outcome,
                COUNT(*) as count,
                ROUND(COUNT(*)::NUMERIC / SUM(COUNT(*)) OVER (), 4) as percentage
            FROM cases
            WHERE appeal_outcome IS NOT NULL
            GROUP BY appeal_outcome
        """)).fetchall()

        # Top sections
        top_sections = db.execute(text("""
                SELECT
                    section_cited,
                    COUNT(*) as citations,
                    ROUND(
                        SUM(CASE WHEN appeal_outcome = 'allowed' THEN 1 ELSE 0 END)::NUMERIC /
                        NULLIF(COUNT(*), 0),
                        4
                    ) as success_rate
                FROM cases
                WHERE section_cited IS NOT NULL
                GROUP BY section_cited
                ORDER BY COUNT(*) DESC
                LIMIT 5
            """)).fetchall()

        # Ministry rankings
        ministry_rankings = db.execute(text("""
            SELECT
                m.name,
                COUNT(c.id) as total_cases,
                ms.denial_rate,
                ms.override_rate
            FROM ministries m
            LEFT JOIN cases c ON c.ministry_id = m.id
            LEFT JOIN ministry_stats ms ON ms.ministry_id = m.id
            GROUP BY m.name, ms.denial_rate, ms.override_rate
            ORDER BY COUNT(c.id) DESC
            LIMIT 5
        """)).fetchall()

        return {
            "overview": {
                "total_cases": total_cases,
                "total_ministries": total_ministries,
                "outcomes": [
                    {
                        "outcome": row.appeal_outcome,
                        "count": row.count,
                        "percentage": float(row.percentage)
                    }
                    for row in outcomes
                ]
            },
            "top_sections": [
                {
                    "section": row.section_cited,
                    "citations": row.citations,
                    "success_rate": float(row.success_rate) if row.success_rate else 0
                }
                for row in top_sections
            ],
            "top_ministries": [
                {
                    "ministry": row.name,
                    "total_cases": row.total_cases,
                    "denial_rate": float(row.denial_rate) if row.denial_rate else 0,
                    "override_rate": float(row.override_rate) if row.override_rate else 0
                }
                for row in ministry_rankings
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching dashboard stats: {str(e)}")
