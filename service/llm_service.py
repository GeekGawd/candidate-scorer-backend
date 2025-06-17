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
""",
            
            "url_extraction": """
Extract social and professional profile URLs from the provided resume text.

RESUME TEXT:
{resume_text}

Please analyze the resume and extract any social/professional URLs mentioned. Look for:
- GitHub profile URLs
- LinkedIn profile URLs  
- Personal portfolio/website URLs
- Other professional platforms (Stack Overflow, Medium, etc.)

Provide a JSON response with the following format:
{{
    "github_url": "<GitHub URL if found, null if not found>",
    "linkedin_url": "<LinkedIn URL if found, null if not found>",
    "portfolio_url": "<Personal website/portfolio URL if found, null if not found>",
    "other_urls": {{
        "<platform_name>": "<URL>",
        "<platform_name>": "<URL>"
    }},
    "extracted_count": <number of URLs found>,
    "confidence_score": <float 0-100 indicating confidence in extraction>,
    "extraction_notes": "<notes about the extraction process>"
}}

Instructions:
1. Look for explicit URLs in the text
2. Look for profile handles/usernames that can be converted to URLs
3. Be conservative - only extract URLs you're confident about
4. Clean and validate URLs to ensure they're properly formatted
5. For GitHub: Look for github.com URLs or mentions like "GitHub: username"
6. For LinkedIn: Look for linkedin.com URLs or mentions like "LinkedIn: /in/username"
7. For portfolios: Look for personal domains, .dev sites, or explicit portfolio mentions
""",

            "name_extraction": """
Extract the candidate's name from the provided resume text.

RESUME TEXT:
{resume_text}

Please analyze the resume and extract the candidate's full name. Look for:
- Name at the top of the resume
- Contact information sections
- Header information
- Email signatures
- Any clear identification of the person

Provide a JSON response with the following format:
{{
    "full_name": "<candidate's full name if found, null if not found>",
    "first_name": "<first name if extractable, null if not found>",
    "last_name": "<last name if extractable, null if not found>",
    "confidence_score": <float 0-100 indicating confidence in extraction>,
    "extraction_notes": "<notes about where/how the name was found>"
}}

Instructions:
1. Look for the most prominent name mention, typically at the top of the resume
2. Be conservative - only extract names you're confident about
3. Avoid extracting company names, project names, or references
4. The name should clearly identify the resume owner
5. If multiple name variations exist, choose the most complete/formal one
6. Consider common resume formats and header placements
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
    
    def extract_social_urls(self, resume_text: str) -> Dict[str, Any]:
        """Extract social and professional URLs from resume text using LLM"""
        prompt = self.scoring_prompts["url_extraction"].format(
            resume_text=resume_text
        )
        
        try:
            logger.info("Extracting social URLs from resume text using LLM...")
            response = call_llm(prompt, use_cache=True)
            extracted_data = self._parse_json_response(response)
            
            # Validate and clean extracted URLs
            cleaned_data = self._validate_and_clean_urls(extracted_data)
            
            logger.info(f"Successfully extracted {cleaned_data.get('extracted_count', 0)} URLs from resume")
            return cleaned_data
            
        except Exception as e:
            logger.error(f"Failed to extract URLs from resume: {e}")
            return {
                "github_url": None,
                "linkedin_url": None,
                "portfolio_url": None,
                "other_urls": {},
                "extracted_count": 0,
                "confidence_score": 0.0,
                "extraction_notes": f"URL extraction failed: {str(e)}"
            }
    
    def extract_candidate_name(self, resume_text: str) -> Dict[str, Any]:
        """Extract candidate name from resume text using LLM"""
        prompt = self.scoring_prompts["name_extraction"].format(
            resume_text=resume_text
        )
        
        try:
            logger.info("Extracting candidate name from resume text using LLM...")
            response = call_llm(prompt, use_cache=True)
            extracted_data = self._parse_json_response(response)
            
            # Validate and clean extracted name data
            cleaned_data = self._validate_and_clean_name(extracted_data)
            
            logger.info(f"Successfully extracted candidate name: {cleaned_data.get('full_name', 'N/A')}")
            return cleaned_data
            
        except Exception as e:
            logger.error(f"Failed to extract candidate name from resume: {e}")
            return {
                "full_name": None,
                "first_name": None,
                "last_name": None,
                "confidence_score": 0.0,
                "extraction_notes": f"Name extraction failed: {str(e)}"
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
    
    def _validate_and_clean_urls(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean extracted URLs"""
        import re
        
        cleaned_data = extracted_data.copy()
        
        # URL validation patterns
        github_pattern = r'https?://(?:www\.)?github\.com/[\w\-._]+/?'
        linkedin_pattern = r'https?://(?:www\.)?linkedin\.com/in/[\w\-._]+/?'
        url_pattern = r'https?://[\w\-._~:/?#[\]@!$&\'()*+,;=]+'
        
        def validate_url(url: str, pattern: str = None) -> str:
            """Validate and clean a single URL"""
            if not url or url.lower() in ['null', 'none', 'n/a']:
                return None
            
            # Clean the URL
            url = url.strip()
            
            # Add https if missing
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # Validate against pattern if provided
            if pattern and not re.match(pattern, url, re.IGNORECASE):
                return None
            
            # Basic URL validation
            if not re.match(url_pattern, url):
                return None
            
            return url
        
        # Validate specific URLs
        cleaned_data['github_url'] = validate_url(extracted_data.get('github_url'), github_pattern)
        cleaned_data['linkedin_url'] = validate_url(extracted_data.get('linkedin_url'), linkedin_pattern)
        cleaned_data['portfolio_url'] = validate_url(extracted_data.get('portfolio_url'))
        
        # Validate other URLs
        other_urls = extracted_data.get('other_urls', {})
        cleaned_other_urls = {}
        if isinstance(other_urls, dict):
            for platform, url in other_urls.items():
                cleaned_url = validate_url(url)
                if cleaned_url:
                    cleaned_other_urls[platform] = cleaned_url
        
        cleaned_data['other_urls'] = cleaned_other_urls
        
        # Update extracted count
        valid_urls = sum([
            1 if cleaned_data['github_url'] else 0,
            1 if cleaned_data['linkedin_url'] else 0,
            1 if cleaned_data['portfolio_url'] else 0,
            len(cleaned_other_urls)
        ])
        
        cleaned_data['extracted_count'] = valid_urls
        
        return cleaned_data
    
    def _validate_and_clean_name(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean extracted name data"""
        import re
        
        cleaned_data = extracted_data.copy()
        
        def clean_name(name: str) -> str:
            """Clean and validate a name string"""
            if not name or name.lower() in ['null', 'none', 'n/a', '']:
                return None
            
            # Remove extra whitespace and clean the name
            name = name.strip()
            
            # Remove any numbers or special characters (except hyphens and apostrophes)
            name = re.sub(r'[^a-zA-Z\s\-\'\.]', '', name)
            
            # Remove multiple spaces
            name = re.sub(r'\s+', ' ', name)
            
            # Validate that it looks like a name (letters only, reasonable length)
            if len(name) < 2 or len(name) > 100:
                return None
            
            # Check if it's likely a real name (not all caps, not all lowercase unless very short)
            if len(name) > 4 and (name.isupper() or name.islower()):
                # Try to title case it
                name = name.title()
            
            return name.strip()
        
        # Clean individual name components
        cleaned_data['full_name'] = clean_name(extracted_data.get('full_name'))
        cleaned_data['first_name'] = clean_name(extracted_data.get('first_name'))
        cleaned_data['last_name'] = clean_name(extracted_data.get('last_name'))
        
        # If we have first and last name but no full name, construct it
        if not cleaned_data['full_name'] and cleaned_data['first_name'] and cleaned_data['last_name']:
            cleaned_data['full_name'] = f"{cleaned_data['first_name']} {cleaned_data['last_name']}"
        
        # If we have full name but no first/last, try to split it
        elif cleaned_data['full_name'] and not (cleaned_data['first_name'] and cleaned_data['last_name']):
            name_parts = cleaned_data['full_name'].split()
            if len(name_parts) >= 2:
                cleaned_data['first_name'] = name_parts[0]
                cleaned_data['last_name'] = ' '.join(name_parts[1:])
            elif len(name_parts) == 1:
                cleaned_data['first_name'] = name_parts[0]
        
        # Ensure confidence score is valid
        confidence = extracted_data.get('confidence_score', 0.0)
        if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 100:
            confidence = 0.0
        cleaned_data['confidence_score'] = float(confidence)
        
        # Lower confidence if we couldn't extract a proper name
        if not cleaned_data['full_name']:
            cleaned_data['confidence_score'] = 0.0
        
        return cleaned_data
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default scoring configuration"""
        return {
            "technical_skills": {"weight": 0.30, "key_technologies": [], "required_level": "mid"},
            "experience": {"weight": 0.25, "minimum_years": 2, "preferred_years": 5, "industry_relevance": 0.8},
            "education": {"weight": 0.15, "required_degree": "bachelors", "preferred_fields": []},
            "soft_skills": {"weight": 0.20, "key_skills": []},
            "role_specific": {"weight": 0.10, "special_requirements": []}
        } 