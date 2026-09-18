from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class EnvironmentalInput(BaseModel):
    query: Optional[str] = None
    soil_ph: Optional[float] = Field(default=None, ge=0, le=14)
    soil_organic_carbon: Optional[float] = Field(default=None, ge=0)
    soil_moisture: Optional[float] = Field(default=None, ge=0)
    rainfall: Optional[str] = None
    temperature: Optional[str] = None
    land_use: Optional[str] = None
    land_cover: Optional[str] = None
    species_richness: Optional[float] = None
    habitat_diversity: Optional[str] = None
    pollution: Optional[str] = None
    deforestation: Optional[str] = None
    crop: Optional[str] = None
    region: Optional[str] = None
    conversation_id: Optional[str] = None


class ChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: str = Field(min_length=1)
    environmental_context: Dict[str, Any] = Field(default_factory=dict)


class Evidence(BaseModel):
    title: str
    organization: str
    source_url: str
    excerpt: str
    relevance: float


class Interaction(BaseModel):
    signals: List[str]
    relationship: str
    intervention: str
    metrics: List[str]


class Recommendation(BaseModel):
    action: str
    why_it_works: str
    impacted_metrics: List[str]
    time_horizon: str
    confidence: str
    reasoning_chain: List[str] = []
    evidence: List[Evidence]


class AnalysisResponse(BaseModel):
    status: str
    needs_clarification: bool
    clarification_questions: List[str] = Field(default_factory=list)
    summary: str
    environmental_state: Dict[str, Any]
    reasoning_trace: List[str]
    interaction_graph: List[Interaction] = Field(default_factory=list)
    recommendations: List[Recommendation]
    retrieved_evidence: List[Evidence]


class ChatResponse(BaseModel):
    conversation_id: str
    message: str
    extracted_context: Dict[str, Any]
    needs_clarification: bool
    reasoning_chain: List[str] = Field(default_factory=list)
    analysis: Optional[AnalysisResponse] = None
