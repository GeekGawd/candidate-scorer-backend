from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import json

Base = declarative_base()

class Candidate(Base):
    __tablename__ = "candidate"
    
    id = Column(Integer, primary_key=True, index=True)
    resume_text = Column(Text, nullable=False)
    resume_filename = Column(String, nullable=True)
    original_file = Column(LargeBinary, nullable=True)  # Store original file
    job_description = Column(Text, nullable=False)
    profile_urls = Column(Text, nullable=True)  # JSON string for URLs
    verification_data = Column(Text, nullable=True)  # JSON string for crawled data
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationship to evaluation results
    evaluations = relationship("EvaluationResult", back_populates="candidate")
    
    def set_profile_urls(self, urls_dict):
        """Set profile URLs as JSON string"""
        self.profile_urls = json.dumps(urls_dict) if urls_dict else None
    
    def get_profile_urls(self):
        """Get profile URLs as dictionary"""
        return json.loads(self.profile_urls) if self.profile_urls else {}
    
    def set_verification_data(self, data_dict):
        """Set verification data as JSON string"""
        self.verification_data = json.dumps(data_dict) if data_dict else None
    
    def get_verification_data(self):
        """Get verification data as dictionary"""
        return json.loads(self.verification_data) if self.verification_data else {}

class EvaluationResult(Base):
    __tablename__ = "evaluation_result"
    
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidate.id"), nullable=False)
    total_score = Column(Float, nullable=False)
    detailed_scores = Column(Text, nullable=False)  # JSON string
    explanation = Column(Text, nullable=False)
    verification_summary = Column(Text, nullable=True)
    bias_analysis = Column(Text, nullable=True)
    recommendations = Column(Text, nullable=True)  # JSON string
    visualization_data = Column(Text, nullable=True)  # JSON string
    evaluated_at = Column(DateTime, server_default=func.now())
    
    # Relationship to candidate
    candidate = relationship("Candidate", back_populates="evaluations")
    
    # Relationship to bias tracking
    bias_tracks = relationship("BiasTracking", back_populates="evaluation")
    
    def set_detailed_scores(self, scores_dict):
        """Set detailed scores as JSON string"""
        self.detailed_scores = json.dumps(scores_dict)
    
    def get_detailed_scores(self):
        """Get detailed scores as dictionary"""
        return json.loads(self.detailed_scores)
    
    def set_recommendations(self, recommendations_list):
        """Set recommendations as JSON string"""
        self.recommendations = json.dumps(recommendations_list) if recommendations_list else None
    
    def get_recommendations(self):
        """Get recommendations as list"""
        return json.loads(self.recommendations) if self.recommendations else []
    
    def set_visualization_data(self, viz_data):
        """Set visualization data as JSON string"""
        self.visualization_data = json.dumps(viz_data) if viz_data else None
    
    def get_visualization_data(self):
        """Get visualization data as dictionary"""
        return json.loads(self.visualization_data) if self.visualization_data else {}

class BiasTracking(Base):
    __tablename__ = "bias_tracking"
    
    id = Column(Integer, primary_key=True, index=True)
    evaluation_id = Column(Integer, ForeignKey("evaluation_result.id"), nullable=False)
    job_description = Column(Text, nullable=False)
    bias_flags = Column(Text, nullable=True)  # JSON string
    recorded_at = Column(DateTime, server_default=func.now())
    
    # Relationship to evaluation result
    evaluation = relationship("EvaluationResult", back_populates="bias_tracks")
    
    def set_bias_flags(self, flags_dict):
        """Set bias flags as JSON string"""
        self.bias_flags = json.dumps(flags_dict) if flags_dict else None
    
    def get_bias_flags(self):
        """Get bias flags as dictionary"""
        return json.loads(self.bias_flags) if self.bias_flags else {} 