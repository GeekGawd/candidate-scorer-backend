# Postman Curl Commands for Candidate Ranking System API

## Base URL
```
http://localhost:8000
```

## 1. Root Endpoint - Get API Information
```bash
curl --location 'http://localhost:8000/' \
--header 'Accept: application/json'
```

## 2. Health Check
```bash
curl --location 'http://localhost:8000/health' \
--header 'Accept: application/json'
```

## 3. Score Candidate (Main Endpoint) - With Optional Manual URLs
```bash
curl --location 'http://localhost:8000/score' \
--form 'resume_file=@"/path/to/your/resume.pdf"' \
--form 'job_description="We are looking for a Senior Software Engineer with 5+ years of experience in Python, FastAPI, and machine learning. The ideal candidate should have experience with REST APIs, database design, and cloud platforms like AWS. Strong problem-solving skills and ability to work in a team environment are essential."'
```

## 4. Score Candidate (Automatic URL Extraction - Recommended)
```bash
curl --location 'http://localhost:8000/score' \
--form 'resume_file=@"/path/to/your/resume.pdf"' \
--form 'job_description="Senior Python Developer with FastAPI experience required. Must have 3+ years of backend development experience."'
```

**Note**: The system now automatically extracts GitHub, LinkedIn, and portfolio URLs from the resume text using AI. It also extracts the candidate's name from the resume. You only need to provide URLs manually if you want to override the auto-extracted ones.

## 5. List Candidates (Default Pagination)
```bash
curl --location 'http://localhost:8000/candidates' \
--header 'Accept: application/json'
```

## 6. List Candidates (With Pagination Parameters)
```bash
curl --location 'http://localhost:8000/candidates?skip=0&limit=5' \
--header 'Accept: application/json'
```

## 7. API Documentation (Swagger UI)
```bash
curl --location 'http://localhost:8000/docs' \
--header 'Accept: text/html'
```

---

## How to Import into Postman:

### Method 1: Import from Raw Text
1. Copy any of the curl commands above
2. Open Postman
3. Click "Import" button
4. Select "Raw text" tab
5. Paste the curl command
6. Click "Continue" → "Import"

### Method 2: Create Collection Manually
1. Create a new collection called "Candidate Ranking API"
2. Add each endpoint as a new request
3. For the `/score` endpoint:
   - Set method to POST
   - Set URL to `http://localhost:8000/score`
   - Go to Body tab → select "form-data"
   - **Required keys**: `resume_file` (File), `job_description` (Text)
   - **Optional keys**: `github_url` (Text), `linkedin_url` (Text), `portfolio_url` (Text)

### Sample Test Data for `/score` endpoint:

**Required Fields:**
- **resume_file**: Upload any PDF or DOCX resume file (max 10MB)
- **job_description**: "Senior Software Engineer position requiring Python, FastAPI, and PostgreSQL experience. Candidate should have 5+ years of backend development experience with strong API design skills."

**Optional Fields (Auto-extracted if not provided):**
- **github_url**: "https://github.com/johndoe" *(only needed to override auto-extraction)*
- **linkedin_url**: "https://linkedin.com/in/johndoe" *(only needed to override auto-extraction)*
- **portfolio_url**: "https://johndoe.dev" *(only needed to override auto-extraction)*

### Expected Response Status Codes:
- **200**: Successful requests
- **400**: Bad request (invalid file type, missing required fields, file too large)
- **422**: Validation error (improved error handling prevents binary data exposure)
- **500**: Internal server error

### File Requirements:
- **Supported formats**: PDF, DOCX only
- **Maximum file size**: 10MB
- **File must contain readable text** (not just images)
- **File must not be password-protected**

### Notes:
- Replace `/path/to/your/resume.pdf` with the actual path to a resume file
- The API now has improved error handling for corrupted or problematic files
- **NEW**: The system automatically extracts candidate names and social URLs from resume text using AI
- Only `resume_file` and `job_description` are required - all URL fields are optional
- Manual URLs will override auto-extracted ones if provided
- Server should be running on localhost:8000 (adjust URL if different)
- If you get validation errors, check that your file is valid and contains readable text
- **Auto-extraction works best with resumes that explicitly mention profile URLs or usernames**
- **Response now includes candidate name and detailed extraction information** 