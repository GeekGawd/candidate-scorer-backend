import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from fastapi import UploadFile

from service.file_processor import FileProcessor
from service.llm_service import LLMService
from service.verification_service import VerificationService
from schemas import DetailedScore, VisualizationData, ScoreResponse

logger = logging.getLogger(__name__)

class ScoringService:
    """Main service for candidate scoring and evaluation"""
    
    def __init__(self):
        self.file_processor = FileProcessor()
        self.llm_service = LLMService()
        self.verification_service = VerificationService()
    
    async def score_candidate(
        self, 
        resume_file: UploadFile, 
        job_description: str,
        candidate_info: Optional[Dict[str, str]] = None
    ) -> Tuple[str, bytes, Dict[str, Any]]:
        """
        Complete candidate scoring workflow with automatic URL extraction
        
        Args:
            resume_file: FastAPI UploadFile object
            job_description: Job description text
            candidate_info: Optional manually provided candidate profile URLs (will be merged with auto-extracted)
        
        Returns:
            Tuple of (resume_text, file_bytes, evaluation_result)
        """
        try:
            # Step 1: Validate and process resume file
            logger.info(f"Processing resume file: {resume_file.filename}")
            
            # Validate file size
            self.file_processor.validate_file_size(resume_file, max_size_mb=10)
            
            # Extract text and get file content
            resume_text, file_bytes = await self.file_processor.process_resume_file(resume_file)
            
            # Step 2: Extract candidate name from resume text
            logger.info("Extracting candidate name from resume text...")
            extracted_name = self.llm_service.extract_candidate_name(resume_text)
            
            # Step 3: Extract social URLs automatically from resume text
            logger.info("Extracting social URLs from resume text...")
            extracted_urls = self.llm_service.extract_social_urls(resume_text)
            
            # Merge manually provided URLs with auto-extracted ones (manual takes precedence)
            final_candidate_info = {}
            if extracted_urls.get('github_url'):
                final_candidate_info['github_url'] = extracted_urls['github_url']
            if extracted_urls.get('linkedin_url'):
                final_candidate_info['linkedin_url'] = extracted_urls['linkedin_url']
            if extracted_urls.get('portfolio_url'):
                final_candidate_info['portfolio_url'] = extracted_urls['portfolio_url']
            
            # Override with manually provided URLs if available
            if candidate_info:
                for key, value in candidate_info.items():
                    if value and value.strip():  # Only override if manually provided value is not empty
                        final_candidate_info[key] = value
            
            logger.info(f"Final candidate URLs: {list(final_candidate_info.keys())}")
            logger.info(f"Extracted candidate name: {extracted_name.get('full_name', 'N/A')}")
            
            # Step 4: Verify candidate profiles (if any URLs available)
            verification_data = {}
            verification_summary = "No profile verification performed"
            
            if final_candidate_info:
                logger.info("Verifying candidate profiles...")
                try:
                    verification_data = self.verification_service.verify_candidate_profiles(final_candidate_info)
                    verification_summary = verification_data.get('summary', 'Profile verification completed')
                except Exception as e:
                    logger.warning(f"Profile verification failed: {e}")
                    verification_summary = "Profile verification failed"
            
            # Step 5: Perform LLM evaluation
            logger.info("Performing LLM evaluation...")
            evaluation_result = self.llm_service.evaluate_candidate(
                resume_text=resume_text,
                job_description=job_description,
                verification_data=verification_data
            )
            
            # Step 6: Analyze bias
            logger.info("Analyzing potential bias...")
            try:
                bias_analysis_result = self.llm_service.analyze_bias(
                    job_description=job_description,
                    evaluation_summary=str(evaluation_result)
                )
                bias_analysis = bias_analysis_result.get('bias_explanation', 'No bias analysis available')
            except Exception as e:
                logger.warning(f"Bias analysis failed: {e}")
                bias_analysis = "Bias analysis failed"
            
            # Step 7: Generate visualization data
            logger.info("Generating visualization data...")
            visualization_data = self._generate_visualization_data(evaluation_result)
            
            # Step 8: Compile final result
            final_result = {
                'total_score': evaluation_result.get('total_score', 0.0),
                'detailed_scores': self._format_detailed_scores(evaluation_result.get('detailed_scores', {})),
                'explanation': evaluation_result.get('explanation', 'No explanation available'),
                'verification_summary': verification_summary,
                'bias_analysis': bias_analysis,
                'recommendations': evaluation_result.get('recommendations', []),
                'visualization_data': visualization_data,
                'strengths': evaluation_result.get('strengths', []),
                'weaknesses': evaluation_result.get('weaknesses', []),
                'raw_evaluation': evaluation_result,  # Store raw LLM output
                'extracted_urls': extracted_urls,  # Include URL extraction results
                'final_candidate_info': final_candidate_info,  # Include final merged URLs
                'extracted_name': extracted_name  # Include extracted name data
            }
            
            logger.info(f"Candidate scoring completed. Total score: {final_result['total_score']}")
            return resume_text, file_bytes, final_result
            
        except Exception as e:
            logger.error(f"Candidate scoring failed: {e}")
            raise ValueError(f"Failed to score candidate: {e}")
    
    def _format_detailed_scores(self, detailed_scores: Dict[str, Any]) -> Dict[str, DetailedScore]:
        """Format detailed scores into proper schema format"""
        formatted_scores = {}
        
        for category, score_data in detailed_scores.items():
            if isinstance(score_data, dict):
                formatted_scores[category] = DetailedScore(
                    score=score_data.get('score', 0.0),
                    evidence=score_data.get('evidence', 'No evidence provided'),
                    breakdown=score_data.get('breakdown', {})
                )
            else:
                # Handle case where score_data is just a number
                formatted_scores[category] = DetailedScore(
                    score=float(score_data) if score_data else 0.0,
                    evidence='Score provided without detailed evidence',
                    breakdown={}
                )
        
        return formatted_scores
    
    def _generate_visualization_data(self, evaluation_result: Dict[str, Any]) -> VisualizationData:
        """Generate data for visualization charts"""
        try:
            detailed_scores = evaluation_result.get('detailed_scores', {})
            
            # Radar chart data (for skills overview)
            radar_data = []
            for category, score_data in detailed_scores.items():
                score = score_data.get('score', 0) if isinstance(score_data, dict) else score_data
                radar_data.append({
                    'category': category.replace('_', ' ').title(),
                    'score': float(score) if score else 0.0
                })
            
            # Bar chart data (detailed breakdown)
            bar_data = []
            for category, score_data in detailed_scores.items():
                if isinstance(score_data, dict) and 'breakdown' in score_data:
                    breakdown = score_data['breakdown']
                    for subcategory, subscore in breakdown.items():
                        bar_data.append({
                            'category': category.replace('_', ' ').title(),
                            'subcategory': subcategory.replace('_', ' ').title(),
                            'score': float(subscore) if subscore else 0.0
                        })
            
            # Score breakdown for pie chart or summary
            score_breakdown = {}
            for category, score_data in detailed_scores.items():
                score = score_data.get('score', 0) if isinstance(score_data, dict) else score_data
                score_breakdown[category.replace('_', ' ').title()] = float(score) if score else 0.0
            
            return VisualizationData(
                radar_chart=radar_data,
                bar_chart=bar_data,
                score_breakdown=score_breakdown
            )
        except Exception as e:
            logger.error(f"Failed to generate visualization data: {e}")
            return VisualizationData()
    
    def get_scoring_insights(self, evaluation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate additional insights from evaluation result"""
        insights = {
            'performance_summary': '',
            'ranking_category': '',
            'improvement_priority': [],
            'competitive_advantages': []
        }
        
        try:
            total_score = evaluation_result.get('total_score', 0)
            
            # Performance summary
            if total_score >= 85:
                insights['performance_summary'] = 'Exceptional candidate with strong qualifications'
                insights['ranking_category'] = 'Top Tier'
            elif total_score >= 70:
                insights['performance_summary'] = 'Strong candidate with good qualifications'
                insights['ranking_category'] = 'High Quality'
            elif total_score >= 55:
                insights['performance_summary'] = 'Adequate candidate with some qualifications'
                insights['ranking_category'] = 'Mid Level'
            else:
                insights['performance_summary'] = 'Candidate may need additional development'
                insights['ranking_category'] = 'Developing'
            
            # Identify improvement priorities (lowest scoring areas)
            detailed_scores = evaluation_result.get('detailed_scores', {})
            if detailed_scores:
                score_items = []
                for category, score_data in detailed_scores.items():
                    score = score_data.get('score', 0) if isinstance(score_data, dict) else score_data
                    score_items.append((category, float(score) if score else 0.0))
                
                # Sort by score and get lowest 2-3
                sorted_scores = sorted(score_items, key=lambda x: x[1])
                insights['improvement_priority'] = [
                    category.replace('_', ' ').title() for category, _ in sorted_scores[:3]
                ]
                
                # Get top strengths (highest scoring areas)
                insights['competitive_advantages'] = [
                    category.replace('_', ' ').title() for category, _ in sorted_scores[-3:]
                ]
            
        except Exception as e:
            logger.error(f"Failed to generate insights: {e}")
        
        return insights 