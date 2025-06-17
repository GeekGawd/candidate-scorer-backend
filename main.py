from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import logging
from contextlib import asynccontextmanager

# Import schemas and models
from schemas import ScoreRequest, ScoreResponse, ErrorResponse
from models import Candidate, EvaluationResult, BiasTracking
from database import get_db, create_tables
from service.scoring_service import ScoringService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Candidate Ranking System...")
    create_tables()
    logger.info("Database tables created/verified")
    yield
    # Shutdown
    logger.info("Shutting down Candidate Ranking System...")

# Initialize FastAPI app
app = FastAPI(
    title="Candidate Ranking System",
    description="AI-powered candidate evaluation and ranking system",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
scoring_service = ScoringService()

@app.get("/")
async def root():
    """Root endpoint with system information"""
    return {
        "message": "Candidate Ranking System API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "score": "/score - POST - Main scoring endpoint",
            "health": "/health - GET - Health check",
            "docs": "/docs - GET - API documentation"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",
        "services": {
            "database": "connected",
            "llm": "available",
            "file_processor": "ready"
        }
    }

@app.post("/score", response_model=ScoreResponse)
async def score_candidate(
    request: ScoreRequest,
    db: Session = Depends(get_db)
):
    """
    Main candidate scoring endpoint
    
    Upload a resume file and job description to get comprehensive candidate evaluation
    """
    try:
        logger.info(f"Received scoring request for {request.file_type} file")
        
        # Extract candidate info
        candidate_info = {}
        if request.candidate_info:
            if request.candidate_info.github_url:
                candidate_info['github_url'] = request.candidate_info.github_url
            if request.candidate_info.linkedin_url:
                candidate_info['linkedin_url'] = request.candidate_info.linkedin_url
            if request.candidate_info.portfolio_url:
                candidate_info['portfolio_url'] = request.candidate_info.portfolio_url
        
        # Process candidate scoring
        resume_text, file_bytes, evaluation_result = await scoring_service.score_candidate(
            resume_file=request.resume_file,
            file_type=request.file_type,
            job_description=request.job_description,
            candidate_info=candidate_info,
            resume_filename=f"resume.{request.file_type}"
        )
        
        # Save candidate to database
        candidate = Candidate(
            resume_text=resume_text,
            resume_filename=f"resume.{request.file_type}",
            original_file=file_bytes,
            job_description=request.job_description
        )
        candidate.set_profile_urls(candidate_info)
        
        db.add(candidate)
        db.commit()
        db.refresh(candidate)
        
        # Save evaluation result
        evaluation = EvaluationResult(
            candidate_id=candidate.id,
            total_score=evaluation_result['total_score'],
            explanation=evaluation_result['explanation'],
            verification_summary=evaluation_result.get('verification_summary'),
            bias_analysis=evaluation_result.get('bias_analysis')
        )
        
        # Convert detailed scores for storage
        detailed_scores_dict = {}
        for category, score_obj in evaluation_result['detailed_scores'].items():
            detailed_scores_dict[category] = {
                'score': score_obj.score,
                'evidence': score_obj.evidence,
                'breakdown': score_obj.breakdown
            }
        
        evaluation.set_detailed_scores(detailed_scores_dict)
        evaluation.set_recommendations(evaluation_result.get('recommendations', []))
        evaluation.set_visualization_data({
            'radar_chart': evaluation_result['visualization_data'].radar_chart,
            'bar_chart': evaluation_result['visualization_data'].bar_chart,
            'score_breakdown': evaluation_result['visualization_data'].score_breakdown
        })
        
        db.add(evaluation)
        db.commit()
        db.refresh(evaluation)
        
        # Save bias tracking
        if evaluation_result.get('bias_analysis'):
            bias_track = BiasTracking(
                evaluation_id=evaluation.id,
                job_description=request.job_description
            )
            bias_track.set_bias_flags({
                'analysis': evaluation_result['bias_analysis'],
                'timestamp': str(evaluation.evaluated_at)
            })
            db.add(bias_track)
            db.commit()
        
        # Return response
        response = ScoreResponse(
            candidate_id=candidate.id,
            total_score=evaluation_result['total_score'],
            detailed_scores=evaluation_result['detailed_scores'],
            verification_summary=evaluation_result.get('verification_summary'),
            explanation=evaluation_result['explanation'],
            bias_analysis=evaluation_result.get('bias_analysis'),
            recommendations=evaluation_result.get('recommendations', []),
            visualization_data=evaluation_result['visualization_data']
        )
        
        logger.info(f"Successfully scored candidate {candidate.id} with score {evaluation_result['total_score']}")
        return response
        
    except ValueError as e:
        logger.error(f"Validation error in scoring: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in scoring: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during candidate scoring"
        )

@app.get("/candidates")
async def list_candidates(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """List evaluated candidates"""
    try:
        candidates = db.query(Candidate).offset(skip).limit(limit).all()
        
        result = []
        for candidate in candidates:
            candidate_data = {
                'id': candidate.id,
                'resume_filename': candidate.resume_filename,
                'job_description': candidate.job_description[:200] + "..." if len(candidate.job_description) > 200 else candidate.job_description,
                'created_at': candidate.created_at,
                'profile_urls': candidate.get_profile_urls(),
                'evaluations_count': len(candidate.evaluations)
            }
            
            # Get latest evaluation score if available
            if candidate.evaluations:
                latest_eval = sorted(candidate.evaluations, key=lambda x: x.evaluated_at, reverse=True)[0]
                candidate_data['latest_score'] = latest_eval.total_score
                candidate_data['latest_evaluation_date'] = latest_eval.evaluated_at
            
            result.append(candidate_data)
        
        return {
            'candidates': result,
            'total': db.query(Candidate).count(),
            'skip': skip,
            'limit': limit
        }
    except Exception as e:
        logger.error(f"Error listing candidates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve candidates"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 