"""
Knowledge Graph API Endpoint
Returns the RTI case knowledge graph showing relationships between ministries, sections, and outcomes
Dynamically generated from database in real-time
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, List, Any
from collections import defaultdict
import re

from ..database import get_db
from ..models import Case

router = APIRouter(prefix="/api", tags=["graph"])

def extract_sections(text: str) -> List[str]:
    """Extract RTI Act section references from text."""
    if not text:
        return []

    # Match patterns like "Section 8(1)", "Section 2(f)", "Sec 6", etc.
    patterns = [
        r'Section\s+(\d+(?:\([a-z0-9]+\))?)',
        r'Sec\.\s+(\d+(?:\([a-z0-9]+\))?)',
        r'Sec\s+(\d+(?:\([a-z0-9]+\))?)',
    ]

    sections = set()
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        sections.update(matches)

    return list(sections)

@router.get("/graph")
async def get_knowledge_graph(db: Session = Depends(get_db)):
    """
    Dynamically generate knowledge graph from database showing relationships between:
    - Ministries (which ministries cite which sections)
    - Sections (which sections lead to which outcomes)
    - Outcomes (allowed, denied, partially_allowed)

    Returns:
        nodes: List of graph nodes with id, name, and type
        edges: List of graph edges with source, target, type, and weight
        metadata: Graph statistics
    """
    try:
        # Fetch all cases from database
        cases = db.query(Case).all()

        if not cases:
            return {
                "nodes": [],
                "edges": [],
                "metadata": {
                    "total_cases": 0,
                    "total_nodes": 0,
                    "total_edges": 0
                }
            }

        # Build graph structure
        nodes = []
        edges = []
        node_ids = {}
        edge_counts = defaultdict(int)

        # Track unique entities
        ministries = set()
        sections = set()
        outcomes = set()

        # Extract relationships from cases
        for case in cases:
            # Extract ministry/department
            if case.department:
                ministries.add(case.department)

            # Extract sections from case text
            case_text = f"{case.case_title or ''} {case.summary or ''} {case.full_text or ''}"
            case_sections = extract_sections(case_text)
            sections.update(case_sections)

            # Extract outcome
            if case.outcome:
                outcomes.add(case.outcome)

            # Build edges: ministry -> section -> outcome
            if case.department and case.outcome:
                for section in case_sections:
                    # Ministry -> Section
                    edge_key = (case.department, f"Section {section}", "cites")
                    edge_counts[edge_key] += 1

                    # Section -> Outcome
                    edge_key = (f"Section {section}", case.outcome, "leads_to")
                    edge_counts[edge_key] += 1

        # Create nodes
        node_id = 0

        # Ministry nodes
        for ministry in sorted(ministries):
            node_ids[ministry] = f"ministry_{node_id}"
            nodes.append({
                "id": f"ministry_{node_id}",
                "name": ministry,
                "type": "ministry"
            })
            node_id += 1

        # Section nodes
        for section in sorted(sections):
            section_name = f"Section {section}"
            node_ids[section_name] = f"section_{node_id}"
            nodes.append({
                "id": f"section_{node_id}",
                "name": section_name,
                "type": "section"
            })
            node_id += 1

        # Outcome nodes
        for outcome in sorted(outcomes):
            node_ids[outcome] = f"outcome_{node_id}"
            nodes.append({
                "id": f"outcome_{node_id}",
                "name": outcome,
                "type": "outcome"
            })
            node_id += 1

        # Create edges with weights
        for (source, target, edge_type), count in edge_counts.items():
            if source in node_ids and target in node_ids:
                edges.append({
                    "source": node_ids[source],
                    "target": node_ids[target],
                    "type": edge_type,
                    "weight": count
                })

        # Calculate metadata
        metadata = {
            "total_cases": len(cases),
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "ministries_count": len(ministries),
            "sections_count": len(sections),
            "outcomes_count": len(outcomes),
            "generated_at": "real-time"
        }

        return {
            "nodes": nodes,
            "edges": edges,
            "metadata": metadata
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating knowledge graph: {str(e)}"
        )
