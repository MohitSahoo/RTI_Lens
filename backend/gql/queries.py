"""
GraphQL Query and Mutation Definitions
"""
import strawberry
from typing import List, Optional

from backend.gql.schema import (
    Ministry, Case, SectionStat, OverrideTrend, KnowledgeGraph,
    DashboardStats, PredictionResult, QAResponse, DraftResponse,
    PredictionInput, QAInput, DraftInput, MinistryFilter, PaginationInput
)
from backend.gql import resolvers


@strawberry.type
class Query:
    """GraphQL Queries"""

    @strawberry.field
    def ministries(self, filter: Optional[MinistryFilter] = None) -> List[Ministry]:
        """Get all ministries with denial rates and optional filters"""
        return resolvers.resolve_ministries(filter)

    @strawberry.field
    def section_heatmap(self) -> List[SectionStat]:
        """Get section misuse rates by ministry"""
        return resolvers.resolve_section_heatmap()

    @strawberry.field
    def override_trend(self) -> List[OverrideTrend]:
        """Get appeal override trend over time (last 24 months)"""
        return resolvers.resolve_override_trend()

    @strawberry.field
    def ministry_cases(
        self,
        ministry_id: int,
        pagination: Optional[PaginationInput] = None
    ) -> List[Case]:
        """Get cases for a specific ministry with pagination"""
        return resolvers.resolve_ministry_cases(ministry_id, pagination)

    @strawberry.field
    def knowledge_graph(self) -> KnowledgeGraph:
        """Get knowledge graph with visual metadata for dashboard"""
        return resolvers.resolve_knowledge_graph()

    @strawberry.field
    def dashboard_stats(self) -> DashboardStats:
        """Get dashboard overview statistics"""
        return resolvers.resolve_dashboard_stats()


@strawberry.type
class Mutation:
    """GraphQL Mutations"""

    @strawberry.mutation
    def predict_outcome(self, input: PredictionInput) -> PredictionResult:
        """Predict appeal outcome using ML model"""
        return resolvers.resolve_prediction(input)


# Create schema
schema = strawberry.Schema(query=Query, mutation=Mutation)
