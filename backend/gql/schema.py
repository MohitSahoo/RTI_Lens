"""
GraphQL Schema for RTI-Lens
Defines types, queries, and mutations using Strawberry
"""
import strawberry
from typing import List, Optional
from datetime import date
from backend.enums import AppealLevel

GraphQLAppealLevel = strawberry.enum(AppealLevel)

# ============================================================================
# Core Types
# ============================================================================

@strawberry.type
class Ministry:
    id: int
    name: str
    total_cases: int
    denial_rate: float
    override_rate: Optional[float]


@strawberry.type
class Case:
    id: int
    order_number: str
    order_url: Optional[str]
    ministry_id: int
    section_cited: Optional[str]
    appeal_outcome: Optional[str]
    appeal_level: Optional[str]
    order_date: Optional[date]
    extraction_method: Optional[str]


@strawberry.type
class SectionStat:
    section_cited: str
    ministry: str
    total_citations: int
    overturned_count: int
    misuse_rate: float


@strawberry.type
class OverrideTrend:
    date: str
    allowed_count: int
    denied_count: int
    override_rate: float


# ============================================================================
# Graph Types
# ============================================================================

@strawberry.type
class GraphNode:
    id: int
    name: str
    type: str
    color: str
    importance: float
    in_degree: float
    out_degree: float
    size: Optional[float] = None
    total_cases: Optional[int] = None
    denial_rate: Optional[float] = None
    override_rate: Optional[float] = None
    total_citations: Optional[int] = None
    success_rate: Optional[float] = None
    allowed_count: Optional[int] = None
    denied_count: Optional[int] = None


@strawberry.type
class GraphEdge:
    source: int
    target: int
    type: str
    weight: float
    count: int
    thickness: Optional[float] = None
    color: Optional[str] = None
    animated: Optional[bool] = None


@strawberry.type
class GraphMetadata:
    node_count: int
    edge_count: int
    ministries: int
    sections: int
    outcomes: int


@strawberry.type
class KnowledgeGraph:
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    metadata: GraphMetadata
    layout: Optional[str] = None


# ============================================================================
# Dashboard Types
# ============================================================================

@strawberry.type
class OutcomeDistribution:
    outcome: str
    count: int
    percentage: float


@strawberry.type
class TopSection:
    section: str
    citations: int
    success_rate: float


@strawberry.type
class TopMinistry:
    ministry: str
    total_cases: int
    denial_rate: float
    override_rate: float


@strawberry.type
class DashboardOverview:
    total_cases: int
    total_ministries: int
    outcomes: List[OutcomeDistribution]


@strawberry.type
class DashboardStats:
    overview: DashboardOverview
    top_sections: List[TopSection]
    top_ministries: List[TopMinistry]


# ============================================================================
# ML Prediction Types
# ============================================================================

@strawberry.type
class ModelCard:
    model_type: str
    accuracy: float
    f1: float
    training_size: int
    test_size: int
    disclaimer: str


@strawberry.type
class PredictionResult:
    prediction: str
    probability: float
    confidence: str
    disclaimer: str
    low_data_warning: bool
    model_card: Optional[ModelCard] = None


# ============================================================================
# Q&A Types
# ============================================================================

@strawberry.type
class QASource:
    order_number: str
    score: float
    text: str


@strawberry.type
class QAResponse:
    answer: str
    sources: List[QASource]
    confidence: Optional[str] = None
    calls_remaining: Optional[int] = None
    faithful: Optional[bool] = None


# ============================================================================
# Draft Types
# ============================================================================

@strawberry.type
class ChangeNote:
    type: str
    description: str


@strawberry.type
class DraftResponse:
    improved_query: str
    change_notes: List[ChangeNote]
    avoid_phrases: List[str]
    sources: List[QASource]


# ============================================================================
# Input Types
# ============================================================================

@strawberry.input
class PredictionInput:
    ministry: str
    section_cited: str
    appeal_level: GraphQLAppealLevel
    order_date: Optional[date] = None
    raw_text: str

    def __post_init__(self):
        if len(self.raw_text) < 100:
            raise ValueError("raw_text must be at least 100 characters")


@strawberry.input
class QAInput:
    question: str
    top_k: Optional[int] = 5


@strawberry.input
class DraftInput:
    ministry: str
    section_cited: str
    context: str


@strawberry.input
class MinistryFilter:
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    ministry_id: Optional[int] = None

    def __post_init__(self):
        if (
            self.year_from is not None and
            self.year_to is not None and
            self.year_from > self.year_to
        ):
            raise ValueError("year_from cannot be greater than year_to")


@strawberry.input
class PaginationInput:
    offset: int = 0
    limit: int = 100

    def __post_init__(self):
        if self.offset < 0:
            raise ValueError("offset cannot be negative")
        if self.limit < 1:
            raise ValueError("limit must be at least 1")
        if self.limit > 500:
            raise ValueError("limit cannot exceed 500")
