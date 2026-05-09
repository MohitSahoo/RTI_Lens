"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date
from backend.enums import AppealLevel

class QARequest(BaseModel):
    question: str = Field(..., min_length=10, max_length=500)
    top_k: Optional[int] = Field(5, ge=1, le=20)

class QAResponse(BaseModel):
    answer: str
    sources: List[dict]
    confidence: Optional[str] = None
    confidence_score: Optional[float] = None
    calls_remaining: Optional[int] = None
    faithful: Optional[bool] = None
    session_id: Optional[str] = None
    thread_id: Optional[str] = None

class DraftRequest(BaseModel):
    ministry: str
    section_cited: str
    context: str = Field(..., min_length=50)

class DraftResponse(BaseModel):
    improved_query: str
    change_notes: List[dict]
    avoid_phrases: List[str]
    sources: List[dict]

class PredictRequest(BaseModel):
    ministry: str
    section_cited: str
    appeal_level: AppealLevel
    order_date: Optional[date] = None
    raw_text: str = Field(..., min_length=100)

class PredictResponse(BaseModel):
    prediction: str  # "allowed" or "denied"
    probability: float
    confidence: str
    disclaimer: str
    low_data_warning: Optional[bool] = None
    model_card: Optional[dict] = None

class DenialRateResponse(BaseModel):
    ministry_id: int
    ministry: str
    total_orders: int
    denied_count: int
    allowed_count: int
    denial_rate: float
    override_rate: Optional[float]

class SectionHeatmapResponse(BaseModel):
    section_cited: str
    ministry: str
    total_citations: int
    overturned_count: int
    misuse_rate: float

class OverrideTrendResponse(BaseModel):
    date: str
    allowed_count: int
    denied_count: int
    override_rate: float

class MinistryOrderResponse(BaseModel):
    order_number: str
    order_url: Optional[str]
    section_cited: Optional[str]
    appeal_outcome: Optional[str]
    appeal_level: Optional[str]
    order_date: Optional[date]

class GraphNode(BaseModel):
    id: str
    type: str  # 'ministry', 'section', or 'outcome'

class GraphEdge(BaseModel):
    source: str
    target: str
    weight: float
    edge_type: str  # 'cites' or 'leads_to'
    count: Optional[int] = None

class GraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
