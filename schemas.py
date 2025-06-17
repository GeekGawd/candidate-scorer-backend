from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime

# Form-data Request Models (no longer need ScoreRequest as we'll use Form parameters)
class CandidateInfoForm(BaseModel):
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None

# Response Models
class DetailedScore(BaseModel):
    score: float = Field(..., ge=0, le=100)
    evidence: str
    breakdown: Optional[Dict[str, Any]] = None

class VisualizationData(BaseModel):
    radar_chart: List[Dict[str, Any]] = []
    bar_chart: List[Dict[str, Any]] = []
    score_breakdown: Dict[str, float] = {}

class ExtractedUrls(BaseModel):
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    other_urls: Dict[str, str] = {}
    extracted_count: int = 0
    confidence_score: float = 0.0
    extraction_notes: str = ""

class ExtractedName(BaseModel):
    full_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    confidence_score: float = 0.0
    extraction_notes: str = ""

class ScoreResponse(BaseModel):
    candidate_id: int
    candidate_name: Optional[str] = None
    total_score: float = Field(..., ge=0, le=100)
    detailed_scores: Dict[str, DetailedScore]
    verification_summary: Optional[str] = None
    explanation: str
    bias_analysis: Optional[str] = None
    recommendations: List[str] = []
    visualization_data: VisualizationData
    extracted_urls: Optional[ExtractedUrls] = None
    extracted_name: Optional[ExtractedName] = None
    final_candidate_urls: Dict[str, str] = {}

# Database Models (for ORM)
class CandidateBase(BaseModel):
    resume_text: str
    resume_filename: Optional[str] = None
    job_description: str

class CandidateCreate(CandidateBase):
    original_file: Optional[bytes] = None
    profile_urls: Optional[Dict[str, str]] = None
    verification_data: Optional[Dict[str, Any]] = None

class CandidateResponse(CandidateBase):
    id: int
    created_at: datetime
    profile_urls: Dict[str, str] = {}
    verification_data: Dict[str, Any] = {}

    class Config:
        from_attributes = True

class EvaluationResultBase(BaseModel):
    total_score: float
    explanation: str
    verification_summary: Optional[str] = None
    bias_analysis: Optional[str] = None

class EvaluationResultCreate(EvaluationResultBase):
    candidate_id: int
    detailed_scores: Dict[str, Any]
    recommendations: Optional[List[str]] = None
    visualization_data: Optional[Dict[str, Any]] = None

class EvaluationResultResponse(EvaluationResultBase):
    id: int
    candidate_id: int
    detailed_scores: Dict[str, Any]
    recommendations: List[str] = []
    visualization_data: Dict[str, Any] = {}
    evaluated_at: datetime

    class Config:
        from_attributes = True

# Configuration Models
class ScoringConfig(BaseModel):
    technical_skills: Dict[str, Any]
    experience: Dict[str, Any]
    education: Dict[str, Any]
    projects_achievements: Dict[str, Any]
    soft_skills: Dict[str, Any]
    resume_quality: Dict[str, Any]
    cultural_fit: Dict[str, Any]

# Error Models
class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now) 