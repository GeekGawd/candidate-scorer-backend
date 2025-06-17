from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import logging
from contextlib import asynccontextmanager
from typing import Optional

# Import schemas and models
from schemas import ScoreResponse, ErrorResponse, ExtractedUrls, ExtractedName
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

# Custom exception handler for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Custom handler for validation errors to prevent binary data exposure
    """
    # Filter out any errors that might contain binary data
    safe_errors = []
    for error in exc.errors():
        safe_error = {
            "type": error.get("type", "validation_error"),
            "loc": error.get("loc", []),
            "msg": error.get("msg", "Validation error")
        }
        # Don't include the actual input value to avoid binary data
        safe_errors.append(safe_error)
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": safe_errors,
            "message": "Request validation failed. Please check your file and form data."
        }
    )

@app.get("/")
async def root():
    """Root endpoint with system information"""
    return {
        "message": "Candidate Ranking System API",
        "version": "1.0.0",
        "status": "running",
        "features": [
            "AI-powered candidate evaluation",
            "Automatic candidate name extraction",
            "Automatic social URL extraction from resumes",
            "Profile verification and bias analysis",
            "Comprehensive scoring with detailed breakdowns"
        ],
        "endpoints": {
            "score": "/score - POST - Main scoring endpoint with auto URL extraction (form-data)",
            "health": "/health - GET - Health check",
            "candidates": "/candidates - GET - List evaluated candidates",
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
    resume_file: UploadFile = File(..., description="Resume file (PDF or DOCX)"),
    job_description: str = Form(..., description="Job description text"),
    github_url: Optional[str] = Form(None, description="GitHub profile URL (optional - will be auto-extracted from resume if not provided)"),
    linkedin_url: Optional[str] = Form(None, description="LinkedIn profile URL (optional - will be auto-extracted from resume if not provided)"),
    portfolio_url: Optional[str] = Form(None, description="Portfolio website URL (optional - will be auto-extracted from resume if not provided)"),
    db: Session = Depends(get_db)
):
    """
    Main candidate scoring endpoint with automatic data extraction
    
    Upload a resume file and job description to get comprehensive candidate evaluation.
    The system will automatically extract:
    - Candidate name from the resume
    - Social/professional URLs (GitHub, LinkedIn, portfolio)
    
    You can optionally provide URLs manually which will override the auto-extracted ones.
    """
    try:
        logger.info(f"Received scoring request for file: {resume_file.filename}")
        
        # Validate file type early to prevent binary data issues
        if not resume_file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No filename provided"
            )
        
        file_extension = resume_file.filename.lower().split('.')[-1]
        if file_extension not in ['pdf', 'docx']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported file type. Only PDF and DOCX files are supported."
            )
        
        # Validate file size before processing
        if hasattr(resume_file, 'size') and resume_file.size:
            max_size_bytes = 10 * 1024 * 1024  # 10MB
            if resume_file.size > max_size_bytes:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File size exceeds 10MB limit"
                )
        
        # Prepare manually provided candidate info (these will be merged with auto-extracted URLs)
        manual_candidate_info = {}
        if github_url:
            manual_candidate_info['github_url'] = github_url
        if linkedin_url:
            manual_candidate_info['linkedin_url'] = linkedin_url
        if portfolio_url:
            manual_candidate_info['portfolio_url'] = portfolio_url
        
        # Process candidate scoring with proper error handling (includes automatic URL extraction)
        try:
            resume_text, file_bytes, evaluation_result = await scoring_service.score_candidate(
                resume_file=resume_file,
                job_description=job_description,
                candidate_info=manual_candidate_info if manual_candidate_info else None
            )
        except ValueError as ve:
            # Handle file processing and validation errors
            logger.error(f"File processing error: {ve}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(ve)
            )
        except Exception as e:
            # Handle unexpected errors during scoring
            logger.error(f"Unexpected error during scoring: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process the resume file. Please ensure the file is valid and try again."
            )
        
        # Get final candidate URLs (combination of auto-extracted and manually provided)
        final_candidate_urls = evaluation_result.get('final_candidate_info', {})
        
        # Get extracted candidate name
        extracted_name_data = evaluation_result.get('extracted_name', {})
        candidate_name = extracted_name_data.get('full_name')
        
        # Save candidate to database
        candidate = Candidate(
            candidate_name=candidate_name,
            resume_text=resume_text,
            resume_filename=resume_file.filename,
            original_file=file_bytes,
            job_description=job_description
        )
        candidate.set_profile_urls(final_candidate_urls)
        
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
                job_description=job_description
            )
            bias_track.set_bias_flags({
                'analysis': evaluation_result['bias_analysis'],
                'timestamp': str(evaluation.evaluated_at)
            })
            db.add(bias_track)
            db.commit()
        
        # Prepare extracted URLs for response
        extracted_urls_data = evaluation_result.get('extracted_urls', {})
        extracted_urls = ExtractedUrls(
            github_url=extracted_urls_data.get('github_url'),
            linkedin_url=extracted_urls_data.get('linkedin_url'),
            portfolio_url=extracted_urls_data.get('portfolio_url'),
            other_urls=extracted_urls_data.get('other_urls', {}),
            extracted_count=extracted_urls_data.get('extracted_count', 0),
            confidence_score=extracted_urls_data.get('confidence_score', 0.0),
            extraction_notes=extracted_urls_data.get('extraction_notes', '')
        )
        
        # Prepare extracted name for response
        extracted_name = ExtractedName(
            full_name=extracted_name_data.get('full_name'),
            first_name=extracted_name_data.get('first_name'),
            last_name=extracted_name_data.get('last_name'),
            confidence_score=extracted_name_data.get('confidence_score', 0.0),
            extraction_notes=extracted_name_data.get('extraction_notes', '')
        )
        
        # Return response
        response = ScoreResponse(
            candidate_id=candidate.id,
            candidate_name=candidate_name,
            total_score=evaluation_result['total_score'],
            detailed_scores=evaluation_result['detailed_scores'],
            verification_summary=evaluation_result.get('verification_summary'),
            explanation=evaluation_result['explanation'],
            bias_analysis=evaluation_result.get('bias_analysis'),
            recommendations=evaluation_result.get('recommendations', []),
            visualization_data=evaluation_result['visualization_data'],
            extracted_urls=extracted_urls,
            extracted_name=extracted_name,
            final_candidate_urls=final_candidate_urls
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
                'candidate_name': candidate.candidate_name,
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