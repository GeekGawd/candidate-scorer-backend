import json
import logging
from typing import Dict, Any, Optional, List
from call_llm import call_llm

logger = logging.getLogger(__name__)

class LLMService:
    """Enhanced LLM service for candidate evaluation"""
    
    def __init__(self):
        self.scoring_prompts = {
            "candidate_evaluation": """
You are an expert HR recruiter and candidate evaluation specialist. Analyze the provided resume and job description to give a comprehensive candidate evaluation.

RESUME TEXT:
{resume_text}

JOB DESCRIPTION:
{job_description}

VERIFICATION DATA (if available):
{verification_data}

Please provide a structured JSON response with the following format:
{{
    "total_score": <float between 0-100>,
    "detailed_scores": {{
        "technical_skills": {{
            "score": <float 0-100>,
            "evidence": "<specific evidence from resume>",
            "breakdown": {{
                "programming_languages": <float 0-100>,
                "frameworks_libraries": <float 0-100>,
                "databases": <float 0-100>,
                "cloud_devops": <float 0-100>
            }}
        }},
        "experience": {{
            "score": <float 0-100>,
            "evidence": "<specific evidence from resume>",
            "breakdown": {{
                "total_years": <float 0-100>,
                "relevant_years": <float 0-100>,
                "company_tier": <float 0-100>
            }}
        }},
        "education": {{
            "score": <float 0-100>,
            "evidence": "<specific evidence from resume>",
            "breakdown": {{
                "degree_level": <float 0-100>,
                "institution_reputation": <float 0-100>,
                "relevance": <float 0-100>
            }}
        }},
        "projects_achievements": {{
            "score": <float 0-100>,
            "evidence": "<specific evidence from resume>",
            "breakdown": {{
                "complexity": <float 0-100>,
                "impact": <float 0-100>,
                "innovation": <float 0-100>
            }}
        }},
        "soft_skills": {{
            "score": <float 0-100>,
            "evidence": "<specific evidence from resume>",
            "breakdown": {{
                "leadership": <float 0-100>,
                "communication": <float 0-100>,
                "problem_solving": <float 0-100>
            }}
        }}
    }},
    "explanation": "<detailed explanation of scoring reasoning>",
    "recommendations": [
        "<specific improvement suggestions>"
    ],
    "strengths": [
        "<key candidate strengths>"
    ],
    "weaknesses": [
        "<areas for improvement>"
    ]
}}

Focus on:
1. Match between candidate skills and job requirements
2. Evidence-based scoring with specific examples
3. Contextual understanding beyond keyword matching
4. Fair and unbiased evaluation
""",
            
            "bias_analysis": """
Analyze the following job description and evaluation process for potential bias:

JOB DESCRIPTION:
{job_description}

EVALUATION RESULTS:
{evaluation_summary}

Provide a JSON response analyzing potential bias:
{{
    "bias_detected": <boolean>,
    "bias_types": [
        "<list of potential bias types if any>"
    ],
    "bias_explanation": "<explanation of detected biases>",
    "suggestions": [
        "<suggestions to reduce bias>"
    ],
    "fairness_score": <float 0-100>
}}

Look for:
- Gender, age, cultural, or educational bias
- Overemphasis on specific company names
- Unrealistic requirements
- Biased language in job description
""",
            
            "verification_summary": """
Cross-reference the resume with the following profile data:

RESUME CLAIMS:
{resume_text}

PROFILE DATA:
{profile_data}

Provide a JSON summary:
{{
    "verification_score": <float 0-100>,
    "consistency_analysis": "<detailed analysis>",
    "discrepancies": [
        "<list of any discrepancies found>"
    ],
    "additional_evidence": [
        "<additional positive evidence from profiles>"
    ],
    "profile_summary": "<summary of profile activities and contributions>"
}}
"""
        }
    
    def generate_scoring_config(self, job_description: str) -> Dict[str, Any]:
        """Generate dynamic scoring configuration based on job description"""
        prompt = f"""
Analyze this job description and create a scoring configuration:

JOB DESCRIPTION:
{job_description}

Generate a JSON configuration that weights different evaluation criteria based on the job requirements:

{{
    "technical_skills": {{
        "weight": <float 0-1>,
        "key_technologies": ["<list of important technologies>"],
        "required_level": "<junior|mid|senior|expert>"
    }},
    "experience": {{
        "weight": <float 0-1>,
        "minimum_years": <int>,
        "preferred_years": <int>,
        "industry_relevance": <float 0-1>
    }},
    "education": {{
        "weight": <float 0-1>,
        "required_degree": "<level if specified>",
        "preferred_fields": ["<relevant fields>"]
    }},
    "soft_skills": {{
        "weight": <float 0-1>,
        "key_skills": ["<important soft skills for this role>"]
    }},
    "role_specific": {{
        "weight": <float 0-1>,
        "special_requirements": ["<any special requirements>"]
    }}
}}

Ensure all weights sum to 1.0.
"""
        
        try:
            response = call_llm(prompt, use_cache=True)
            return self._parse_json_response(response)
        except Exception as e:
            logger.error(f"Failed to generate scoring config: {e}")
            # Return default config
            return self._get_default_config()
    
    def evaluate_candidate(self, resume_text: str, job_description: str, 
                          verification_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Perform comprehensive candidate evaluation"""
        verification_str = json.dumps(verification_data, indent=2) if verification_data else "No verification data available"
        
        prompt = self.scoring_prompts["candidate_evaluation"].format(
            resume_text=resume_text,
            job_description=job_description,
            verification_data=verification_str
        )
        
        try:
            response = call_llm(prompt, use_cache=True)
            return self._parse_json_response(response)
        except Exception as e:
            logger.error(f"Failed to evaluate candidate: {e}")
            raise ValueError(f"Candidate evaluation failed: {e}")
    
    def analyze_bias(self, job_description: str, evaluation_summary: str) -> Dict[str, Any]:
        """Analyze potential bias in job description and evaluation"""
        prompt = self.scoring_prompts["bias_analysis"].format(
            job_description=job_description,
            evaluation_summary=evaluation_summary
        )
        
        try:
            response = call_llm(prompt, use_cache=True)
            return self._parse_json_response(response)
        except Exception as e:
            logger.error(f"Failed to analyze bias: {e}")
            return {
                "bias_detected": False,
                "bias_types": [],
                "bias_explanation": "Bias analysis failed",
                "suggestions": [],
                "fairness_score": 50.0
            }
    
    def verify_candidate_data(self, resume_text: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify candidate data against profile information"""
        prompt = self.scoring_prompts["verification_summary"].format(
            resume_text=resume_text,
            profile_data=json.dumps(profile_data, indent=2)
        )
        
        try:
            response = call_llm(prompt, use_cache=True)
            return self._parse_json_response(response)
        except Exception as e:
            logger.error(f"Failed to verify candidate data: {e}")
            return {
                "verification_score": 50.0,
                "consistency_analysis": "Verification failed",
                "discrepancies": [],
                "additional_evidence": [],
                "profile_summary": "Could not analyze profile data"
            }
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON response from LLM, handling potential formatting issues"""
        try:
            # Try to find JSON in the response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON found in response")
            
            json_str = response[start_idx:end_idx]
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            logger.error(f"Response was: {response}")
            raise ValueError(f"Invalid JSON response: {e}")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default scoring configuration"""
        return {
            "technical_skills": {"weight": 0.30, "key_technologies": [], "required_level": "mid"},
            "experience": {"weight": 0.25, "minimum_years": 2, "preferred_years": 5, "industry_relevance": 0.8},
            "education": {"weight": 0.15, "required_degree": "bachelors", "preferred_fields": []},
            "soft_skills": {"weight": 0.20, "key_skills": []},
            "role_specific": {"weight": 0.10, "special_requirements": []}
        } 