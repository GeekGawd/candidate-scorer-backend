#!/usr/bin/env python3
"""
Test script for the Candidate Ranking System API
"""

import requests
import json
import os
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def create_sample_resume_pdf():
    """Create a sample resume PDF for testing"""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    
    # Sample resume content
    resume_text = [
        "John Doe",
        "Senior Software Engineer",
        "",
        "Email: john.doe@email.com",
        "Phone: (555) 123-4567",
        "LinkedIn: linkedin.com/in/johndoe",
        "GitHub: github.com/johndoe",
        "",
        "EXPERIENCE:",
        "• Senior Software Engineer at TechCorp (2020-2023)",
        "  - Developed scalable Python applications using Django and FastAPI",
        "  - Built machine learning pipelines with TensorFlow and PyTorch",
        "  - Deployed applications on AWS using Docker and Kubernetes",
        "  - Led a team of 5 engineers and improved system performance by 40%",
        "",
        "• Software Engineer at StartupXYZ (2018-2020)",
        "  - Created REST APIs using Python Flask and PostgreSQL",
        "  - Implemented CI/CD pipelines with GitHub Actions",
        "  - Collaborated with cross-functional teams in Agile environment",
        "",
        "EDUCATION:",
        "• Master of Science in Computer Science",
        "  University of Technology (2016-2018)",
        "",
        "• Bachelor of Science in Software Engineering",
        "  State University (2012-2016)",
        "",
        "SKILLS:",
        "• Programming: Python, JavaScript, TypeScript, Java",
        "• Frameworks: Django, FastAPI, React, Node.js",
        "• Databases: PostgreSQL, MongoDB, Redis",
        "• Cloud: AWS, Docker, Kubernetes, Terraform",
        "• AI/ML: TensorFlow, PyTorch, scikit-learn, pandas",
        "",
        "PROJECTS:",
        "• AI-powered recommendation system (50% increase in user engagement)",
        "• Microservices architecture migration (30% cost reduction)",
        "• Real-time data processing pipeline (handling 1M+ events/day)"
    ]
    
    y_position = 750
    for line in resume_text:
        if y_position < 50:  # Start new page if needed
            c.showPage()
            y_position = 750
        
        c.drawString(50, y_position, line)
        y_position -= 20
    
    c.save()
    buffer.seek(0)
    return buffer.getvalue()

def test_score_api():
    """Test the /score API endpoint"""
    
    # Create sample resume
    pdf_content = create_sample_resume_pdf()
    
    # API endpoint
    url = "http://localhost:8000/score"
    
    # Prepare form data
    files = {
        'resume_file': ('sample_resume.pdf', pdf_content, 'application/pdf')
    }
    
    data = {
        'job_description': """
We are seeking a Senior Software Engineer with 5+ years of experience to join our dynamic team. 

Key Requirements:
- Strong experience with Python and modern web frameworks (Django, FastAPI)
- Experience with machine learning and AI technologies
- Cloud platform experience (AWS, GCP, or Azure)
- Database design and optimization experience
- Strong problem-solving and communication skills
- Experience with microservices and containerization
- Agile development experience

Bonus Points:
- Experience with LLMs and AI model deployment
- DevOps and CI/CD pipeline experience
- Leadership and mentoring experience
        """.strip(),
        'github_url': 'https://github.com/johndoe',
        'linkedin_url': 'https://linkedin.com/in/johndoe',
        'portfolio_url': 'https://johndoe.dev'
    }
    
    try:
        print("Testing /score API endpoint...")
        print(f"URL: {url}")
        print(f"File: sample_resume.pdf ({len(pdf_content)} bytes)")
        print("-" * 50)
        
        response = requests.post(url, files=files, data=data)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success! API Response:")
            print(f"Candidate ID: {result['candidate_id']}")
            print(f"Total Score: {result['total_score']}")
            print(f"Explanation: {result['explanation'][:200]}...")
            print(f"Recommendations: {len(result['recommendations'])} items")
            print(f"Detailed Scores: {list(result['detailed_scores'].keys())}")
        else:
            print("❌ Error!")
            print(f"Response: {response.text}")
    
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Make sure the server is running on localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_health_api():
    """Test the /health API endpoint"""
    url = "http://localhost:8000/health"
    
    try:
        print("Testing /health API endpoint...")
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("✅ Health check passed!")
            print(f"Response: {response.json()}")
        else:
            print("❌ Health check failed!")
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Make sure the server is running on localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Main test function"""
    print("🚀 Candidate Ranking System API Tests")
    print("=" * 50)
    
    # Test health endpoint first
    test_health_api()
    print()
    
    # Test score endpoint
    test_score_api()
    print()
    
    print("📋 Manual Testing Commands:")
    print("-" * 30)
    print("1. Health Check:")
    print("   curl http://localhost:8000/health")
    print()
    print("2. Score API (create your own resume file first):")
    print("""   curl -X POST "http://localhost:8000/score" \\
     -F "resume_file=@your_resume.pdf" \\
     -F "job_description=Your job description here" \\
     -F "github_url=https://github.com/yourusername" \\
     -F "linkedin_url=https://linkedin.com/in/yourusername" \\
     -F "portfolio_url=https://yourportfolio.dev" """)
    print()
    print("3. List Candidates:")
    print("   curl http://localhost:8000/candidates")

if __name__ == "__main__":
    main() 