"""
GraphQL Resolvers for RTI-Lens
Implements queries and mutations using ORM models
"""
from contextlib import contextmanager
from typing import Iterator, List, Optional
from sqlalchemy import func, extract, case as sql_case, Numeric
import json
from pathlib import Path

from backend.database import SessionLocal
from backend.models import Ministry as MinistryModel, Case as CaseModel, MinistryStats, SectionStats
from backend.gql.schema import (
    Ministry, Case, SectionStat, OverrideTrend, KnowledgeGraph, GraphNode, GraphEdge,
    GraphMetadata, DashboardStats, DashboardOverview, OutcomeDistribution, TopSection,
    TopMinistry, PredictionResult, ModelCard, PredictionInput, MinistryFilter, PaginationInput
)


@contextmanager
def get_db_session() -> Iterator:
    """Context-managed database session for GraphQL resolvers."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================================
# Analytics Resolvers
# ============================================================================

def resolve_ministries(filter: Optional[MinistryFilter] = None) -> List[Ministry]:
    """Get all ministries with denial rates"""
    if filter and filter.year_from is not None and filter.year_to is not None and filter.year_from > filter.year_to:
        raise ValueError("year_from cannot be greater than year_to")

    with get_db_session() as db:
        query = db.query(
            MinistryModel.id,
            MinistryModel.name,
            MinistryStats.total_orders,
            MinistryStats.denial_rate,
            MinistryStats.override_rate
        ).join(
            MinistryStats, MinistryModel.id == MinistryStats.ministry_id
        )

        # Apply filters
        if filter:
            if filter.year_from or filter.year_to or filter.ministry_id:
                query = query.join(CaseModel, CaseModel.ministry_id == MinistryModel.id)

                if filter.year_from:
                    query = query.filter(extract('year', CaseModel.order_date) >= filter.year_from)
                if filter.year_to:
                    query = query.filter(extract('year', CaseModel.order_date) <= filter.year_to)
                if filter.ministry_id:
                    query = query.filter(MinistryModel.id == filter.ministry_id)

                query = query.group_by(
                    MinistryModel.id, MinistryModel.name,
                    MinistryStats.total_orders, MinistryStats.denial_rate, MinistryStats.override_rate
                )

        results = query.order_by(MinistryStats.denial_rate.desc()).all()

        return [
            Ministry(
                id=row.id,
                name=row.name,
                total_cases=row.total_orders,
                denial_rate=row.denial_rate,
                override_rate=row.override_rate
            )
            for row in results
        ]


def resolve_section_heatmap() -> List[SectionStat]:
    """Get section misuse rates"""
    with get_db_session() as db:
        results = db.query(
            SectionStats.section_cited,
            MinistryModel.name.label('ministry'),
            SectionStats.total_citations,
            SectionStats.overturned_count,
            SectionStats.misuse_rate
        ).join(
            MinistryModel, MinistryModel.id == SectionStats.ministry_id
        ).order_by(
            SectionStats.misuse_rate.desc()
        ).limit(50).all()

        return [
            SectionStat(
                section_cited=row.section_cited,
                ministry=row.ministry,
                total_citations=row.total_citations,
                overturned_count=row.overturned_count,
                misuse_rate=row.misuse_rate
            )
            for row in results
        ]


def resolve_override_trend() -> List[OverrideTrend]:
    """Get appeal override trend over time"""
    with get_db_session() as db:
        results = db.query(
            func.date_trunc('month', CaseModel.order_date).label('month'),
            func.sum(sql_case((CaseModel.appeal_outcome == 'allowed', 1), else_=0)).label('allowed_count'),
            func.sum(sql_case((CaseModel.appeal_outcome == 'denied', 1), else_=0)).label('denied_count'),
            func.round(
                func.sum(sql_case((CaseModel.appeal_outcome == 'allowed', 1), else_=0)).cast(Numeric) /
                func.nullif(
                    func.sum(sql_case((CaseModel.appeal_outcome.in_(['allowed', 'denied']), 1), else_=0)), 0
                ),
                4
            ).label('override_rate')
        ).filter(
            CaseModel.order_date.isnot(None),
            CaseModel.appeal_outcome.in_(['allowed', 'denied'])
        ).group_by(
            func.date_trunc('month', CaseModel.order_date)
        ).order_by(
            func.date_trunc('month', CaseModel.order_date).desc()
        ).limit(24).all()

        return [
            OverrideTrend(
                date=row.month.strftime('%Y-%m') if row.month else '',
                allowed_count=row.allowed_count or 0,
                denied_count=row.denied_count or 0,
                override_rate=float(row.override_rate) if row.override_rate else 0.0
            )
            for row in results
        ]


def resolve_ministry_cases(ministry_id: int, pagination: Optional[PaginationInput] = None) -> List[Case]:
    """Get cases for a specific ministry"""
    offset = pagination.offset if pagination else 0
    limit = pagination.limit if pagination else 100

    if offset < 0:
        raise ValueError("offset cannot be negative")
    if limit < 1:
        raise ValueError("limit must be at least 1")
    if limit > 500:
        raise ValueError("limit cannot exceed 500")

    with get_db_session() as db:
        results = db.query(CaseModel).filter(
            CaseModel.ministry_id == ministry_id
        ).order_by(
            CaseModel.order_date.desc().nullslast()
        ).offset(offset).limit(limit).all()

        return [
            Case(
                id=case.id,
                order_number=case.order_number,
                order_url=case.order_url,
                ministry_id=case.ministry_id,
                section_cited=case.section_cited,
                appeal_outcome=case.appeal_outcome,
                appeal_level=case.appeal_level,
                order_date=case.order_date,
                extraction_method=case.extraction_method
            )
            for case in results
        ]


# ============================================================================
# Graph Resolvers
# ============================================================================

def resolve_knowledge_graph() -> KnowledgeGraph:
    """Get dashboard knowledge graph"""
    graph_path = Path(__file__).parent.parent.parent / "data" / "dashboard_graph.json"

    if not graph_path.exists():
        raise Exception("Dashboard graph not found. Run scripts/build_dashboard_graph.py first.")

    with open(graph_path, 'r') as f:
        data = json.load(f)

    nodes = [
        GraphNode(
            id=node['id'],
            name=node['name'],
            type=node['type'],
            color=node['color'],
            importance=node['importance'],
            in_degree=node['in_degree'],
            out_degree=node['out_degree'],
            size=node.get('size'),
            total_cases=node.get('total_cases'),
            denial_rate=node.get('denial_rate'),
            override_rate=node.get('override_rate'),
            total_citations=node.get('total_citations'),
            success_rate=node.get('success_rate'),
            allowed_count=node.get('allowed_count'),
            denied_count=node.get('denied_count')
        )
        for node in data['nodes']
    ]

    edges = [
        GraphEdge(
            source=edge['source'],
            target=edge['target'],
            type=edge['type'],
            weight=edge['weight'],
            count=edge['count'],
            thickness=edge.get('thickness'),
            color=edge.get('color'),
            animated=edge.get('animated')
        )
        for edge in data['edges']
    ]

    metadata = GraphMetadata(
        node_count=data['metadata']['node_count'],
        edge_count=data['metadata']['edge_count'],
        ministries=data['metadata']['ministries'],
        sections=data['metadata']['sections'],
        outcomes=data['metadata']['outcomes']
    )

    return KnowledgeGraph(
        nodes=nodes,
        edges=edges,
        metadata=metadata,
        layout=data.get('layout')
    )


# ============================================================================
# Dashboard Resolvers
# ============================================================================

def resolve_dashboard_stats() -> DashboardStats:
    """Get dashboard statistics"""
    with get_db_session() as db:
        # Overall stats
        total_cases = db.query(func.count(CaseModel.id)).scalar() or 0
        total_ministries = db.query(func.count(MinistryModel.id)).scalar() or 0

        # Outcome distribution
        outcomes_data = db.query(
            CaseModel.appeal_outcome.label("appeal_outcome"),
            func.count(CaseModel.id).label("count"),
            func.round(
                func.count(CaseModel.id).cast(Numeric) /
                func.sum(func.count(CaseModel.id)).over(),
                4
            ).label("percentage")
        ).filter(
            CaseModel.appeal_outcome.isnot(None)
        ).group_by(
            CaseModel.appeal_outcome
        ).all()

        outcomes = [
            OutcomeDistribution(
                outcome=row.appeal_outcome,
                count=row.count,
                percentage=float(row.percentage)
            )
            for row in outcomes_data
        ]

        overview = DashboardOverview(
            total_cases=total_cases,
            total_ministries=total_ministries,
            outcomes=outcomes
        )

        # Top sections
        top_sections_data = db.query(
            CaseModel.section_cited.label("section_cited"),
            func.count(CaseModel.id).label("citations"),
            func.round(
                func.sum(
                    sql_case((CaseModel.appeal_outcome == 'allowed', 1), else_=0)
                ).cast(Numeric) / func.nullif(func.count(CaseModel.id), 0),
                4
            ).label("success_rate")
        ).filter(
            CaseModel.section_cited.isnot(None)
        ).group_by(
            CaseModel.section_cited
        ).order_by(
            func.count(CaseModel.id).desc()
        ).limit(5).all()

        top_sections = [
            TopSection(
                section=row.section_cited,
                citations=row.citations,
                success_rate=float(row.success_rate) if row.success_rate else 0
            )
            for row in top_sections_data
        ]

        # Top ministries
        top_ministries_data = db.query(
            MinistryModel.name.label("name"),
            func.count(CaseModel.id).label("total_cases"),
            MinistryStats.denial_rate,
            MinistryStats.override_rate
        ).outerjoin(
            CaseModel, CaseModel.ministry_id == MinistryModel.id
        ).outerjoin(
            MinistryStats, MinistryStats.ministry_id == MinistryModel.id
        ).group_by(
            MinistryModel.id,
            MinistryModel.name,
            MinistryStats.denial_rate,
            MinistryStats.override_rate
        ).order_by(
            func.count(CaseModel.id).desc()
        ).limit(5).all()

        top_ministries = [
            TopMinistry(
                ministry=row.name,
                total_cases=row.total_cases,
                denial_rate=float(row.denial_rate) if row.denial_rate else 0,
                override_rate=float(row.override_rate) if row.override_rate else 0
            )
            for row in top_ministries_data
        ]

        return DashboardStats(
            overview=overview,
            top_sections=top_sections,
            top_ministries=top_ministries
        )


# ============================================================================
# ML Prediction Resolver
# ============================================================================

def resolve_prediction(input: PredictionInput) -> PredictionResult:
    """Predict appeal outcome"""
    import pickle
    import pandas as pd
    from backend.config import MODEL_PATH, MODEL_CARD_PATH

    # Load model
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)

    with open(MODEL_CARD_PATH, "r") as f:
        model_card_data = json.load(f)

    # Prepare input
    year = input.order_date.year if input.order_date else 2024
    input_data = pd.DataFrame([{
        'ministry': input.ministry,
        'section_cited': input.section_cited,
        'appeal_level': input.appeal_level.value,
        'year': year,
        'raw_text': input.raw_text
    }])

    # Predict
    prediction = model.predict(input_data)[0]
    probabilities = model.predict_proba(input_data)[0]

    outcome = "allowed" if prediction == 1 else "denied"
    probability = float(probabilities[1] if prediction == 1 else probabilities[0])

    if probability >= 0.8:
        confidence = "high"
    elif probability >= 0.6:
        confidence = "medium"
    else:
        confidence = "low"

    # Check training data
    with get_db_session() as db:
        ministry_count = db.query(CaseModel).join(
            MinistryModel, CaseModel.ministry_id == MinistryModel.id
        ).filter(MinistryModel.name == input.ministry).count()

    low_data_warning = ministry_count < model_card_data.get("low_data_threshold", 10)

    model_card = ModelCard(
        model_type=model_card_data['model_type'],
        accuracy=model_card_data['accuracy'],
        f1=model_card_data['f1'],
        training_size=model_card_data['training_size'],
        test_size=model_card_data['test_size'],
        disclaimer=model_card_data['disclaimer']
    )

    return PredictionResult(
        prediction=outcome,
        probability=probability,
        confidence=confidence,
        disclaimer=model_card_data['disclaimer'],
        low_data_warning=low_data_warning,
        model_card=model_card
    )
