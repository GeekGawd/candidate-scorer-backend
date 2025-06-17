# Candidate Ranking System Plan

## 1. Introduction

This document outlines a step-by-step plan to implement a Candidate Ranking System in a FastAPI backend. The system will provide:

* Objective, data-driven candidate evaluation
* Configurable scoring criteria and weighting
* Experience level assessment relative to role seniority
* Bias detection and mitigation
* Ranking visualization and explanation

## 2. Architecture Overview

The system will be designed with a modular architecture, centered around a new `LLM Integration Service` to handle all interactions with Large Language Models.

```
+----------------+      +---------------------+      +------------------+
|  FastAPI REST  | <--> |  Business Logic     | <--> |  Database        |
|  Endpoints     |      |  Layer              |      |  (SQLITE3)    |
+----------------+      +---------------------+      +------------------+
                             |           ^
                             v           |
                 +---------------------------+
                 |   LLM Integration Service |<---- (e.g., OpenAI, Anthropic)
                 +---------------------------+
                             |           ^
         +-------------------+-----------+-------------------+
         |                   |                               |
         v                   v                               v
+----------------+  +--------------------------+  +---------------------+
|  Scoring       |  | Enhanced Bias & Fairness |  |  Explanation &      |
|  Engine        |  | Module                   |  |  Visualization      |
+----------------+  +--------------------------+  +---------------------+
```

## 3. Components & Modules

### 3.1 Scoring Engine

*   **Inputs:** Candidate profile (e.g., resume, portfolio link), role description.
*   **Outputs:** Structured JSON with scores, rationale, and extracted evidence.
*   **Features:**
    *   Leverages the `LLM Integration Service` to perform semantic analysis of the candidate's profile against the role requirements.
    *   Goes beyond keyword matching to understand context, proficiency, and impact.
    *   Provides a detailed breakdown of strengths and weaknesses.

### 3.2 Configurable Criteria Service

*   **Natural Language to JSON Config:** Exposes a service where a recruiter can input a natural-language job description. An LLM will then parse this description and generate a detailed, structured `config_json` (like the one in `config.example.json`) with appropriate weights, keywords, and scoring rubrics.
*   **Manual Configuration:** Allows for direct retrieval and updates of the `config_json`, enabling expert users to fine-tune the evaluation criteria.

### 3.3 Candidate Verification & Fairness Module

*   **Resume Verification:**
    *   Crawls public professional profiles (e.g., GitHub, LinkedIn) provided by the candidate.
    *   Uses an LLM to cross-reference the information from these profiles against the claims made in the resume.
    *   Summarizes key activities and contributions (e.g., summarizing a candidate's GitHub projects and activity).
*   **Fairness Analysis:**
    *   Utilizes an LLM to analyze job descriptions for potentially biased or non-inclusive language before they are posted.
    *   Provides suggestions for improving job description clarity and fairness.
    *   Supports analysis of anonymized candidate data to identify and flag potential biases in the scoring process over time.

### 3.4 Explanation & Visualization Service

*   Generates rich, human-readable explanations for each candidate's rank using the rationale provided by the LLM.
*   Translates complex scoring data into intuitive visualizations.
*   Provide data for front-end charts (e.g., JSON payloads for D3.js or similar libraries).
*   Store the detailed LLM output (`raw_scores`) and the main score (`total_score`) in the `candidate_score` table.

### 3.5 LLM Integration Service

*   **Purpose:** A centralized service to manage all interactions with external Large Language Models.
*   **Responsibilities:**
    *   Manages a library of prompts for different tasks (scoring, bias review, explanation).
    *   Handles API calls, including authentication, retries, and error handling.
    *   Parses and validates the structured JSON output from the LLM.
    *   Implements caching to optimize for cost and latency.

## 4. API Design

### 4.1 Primary User API (Simplified)

| Method | Endpoint                             | Description                                            |
| ------ | ------------------------------------ | ------------------------------------------------------ |
| POST   | `/score`                             | **Main API**: Upload resume (Word/PDF) + job description, get comprehensive scoring results |

**Request Format:**
```json
{
  "resume_file": "base64_encoded_file_content",
  "file_type": "pdf|docx",
  "job_description": "text description of the role",
  "candidate_info": {
    "github_url": "optional",
    "linkedin_url": "optional", 
    "portfolio_url": "optional"
  }
}
```

**Response Format:**
```json
{
  "candidate_id": "unique_id",
  "total_score": 85.5,
  "detailed_scores": {
    "technical_skills": {"score": 90, "evidence": "..."},
    "experience": {"score": 80, "evidence": "..."},
    "education": {"score": 85, "evidence": "..."}
  },
  "verification_summary": "Cross-referenced GitHub and LinkedIn...",
  "explanation": "Detailed reasoning for the score...",
  "bias_analysis": "No bias detected in evaluation",
  "recommendations": ["Suggest areas for improvement..."],
  "visualization_data": {
    "radar_chart": [...],
    "bar_chart": [...]
  }
}
```

### 4.2 Administrative APIs (Optional/Internal)

| Method | Endpoint                             | Description                                            |
| ------ | ------------------------------------ | ------------------------------------------------------ |
| GET    | `/config/{role}`                     | Retrieve scoring configuration for a role              |
| PUT    | `/config/{role}`                     | Update scoring configuration                           |
| GET    | `/candidates`                        | List all evaluated candidates                          |
| GET    | `/metrics/bias`                      | Retrieve bias metrics and reports                      |

## 5. Database Schema (SQLITE3)

```sql
-- Candidates (stores resume and extracted data)
CREATE TABLE candidate (
  id                SERIAL PRIMARY KEY,
  resume_text       TEXT NOT NULL,
  resume_filename   TEXT,
  original_file     BYTEA,  -- Store original file for reference
  job_description   TEXT NOT NULL,
  profile_urls      JSONB,  -- GitHub, LinkedIn, portfolio URLs
  verification_data JSONB,  -- Crawled profile data
  created_at        TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Evaluation Results (stores comprehensive scoring)
CREATE TABLE evaluation_result (
  id               SERIAL PRIMARY KEY,
  candidate_id     INTEGER REFERENCES candidate(id),
  total_score      FLOAT NOT NULL,
  detailed_scores  JSONB NOT NULL,  -- Breakdown by category
  explanation      TEXT NOT NULL,
  verification_summary TEXT,
  bias_analysis    TEXT,
  recommendations  JSONB,
  visualization_data JSONB,
  evaluated_at     TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Bias Tracking (for monitoring and improvement)
CREATE TABLE bias_tracking (
  id              SERIAL PRIMARY KEY,
  evaluation_id   INTEGER REFERENCES evaluation_result(id),
  job_description TEXT,
  bias_flags      JSONB,
  recorded_at     TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Simplified Schema Benefits:**
- No complex role configuration management
- Direct storage of file content and results
- Everything linked to individual evaluations
- Bias tracking for continuous improvement

## 6. Single API Workflow Design

When a user calls `POST /score`, the following happens automatically in the background:

1.  **File Processing**: 
    *   Extract text from uploaded Word/PDF resume using libraries like `python-docx` or `PyPDF2`
    *   Parse and clean the extracted text

2.  **Dynamic Configuration Generation**:
    *   Use LLM to analyze the job description and generate a scoring configuration automatically
    *   No need for pre-stored role configs - everything is dynamic based on the job description

3.  **Profile Verification** (if URLs provided):
    *   Crawl GitHub, LinkedIn, or portfolio URLs
    *   Cross-reference information with resume using LLM
    *   Generate verification summary

4.  **Comprehensive Scoring**:
    *   Prepare detailed prompt with job description, resume text, and verification data
    *   Invoke LLM Integration Service for holistic evaluation
    *   Get structured JSON with scores, evidence, and explanations

5.  **Bias Analysis**:
    *   Run bias detection on the job description and scoring process
    *   Include bias analysis in the response

6.  **Response Generation**:
    *   Compile all results into a single comprehensive response
    *   Generate visualization-ready data
    *   Store candidate data and scores in database
    *   Return complete evaluation to user

**Key Benefits of Single API Approach:**
- **Simplicity**: One call does everything
- **No Configuration Management**: Dynamic scoring based on job description
- **Immediate Results**: No need to manage roles, configs, or multi-step processes
- **File Upload Support**: Direct Word/PDF processing

## 7. Verification & Fairness Workflow

1.  **Job Description Analysis:** Before posting a new role, use the `Candidate Verification & Fairness Module` to scan the job description for biased language.
2.  **Candidate Verification:** When a candidate is submitted, automatically crawl their provided public profiles (e.g., GitHub, LinkedIn).
3.  **Information Synthesis:** Use an LLM to summarize the crawled data and cross-reference it with the resume, creating a "verification summary" that is attached to the candidate's profile. This summary is then used as an input for the scoring algorithm.
4.  **Scheduled Audits:** Run a periodic job to analyze aggregate scoring data for statistical disparities.
5.  **Alerting & Logging:** Alert HR or hiring managers of significant bias metrics and log all actions for transparency.

## 8. Explanation & Visualization

All explanation and visualization data is included directly in the single `/score` API response:

*   **Detailed Explanation**: Human-readable breakdown of why the candidate received their score
*   **Evidence-Based Scoring**: Direct quotes and references from the resume supporting each score
*   **Visualization Data**: Ready-to-use JSON arrays for front-end charts (bar charts, radar charts)
*   **Recommendations**: Actionable suggestions for candidate improvement

## 9. Testing Strategy

*   **Unit tests** for scoring functions, config parsing, bias checks.
*   **Integration tests** for API endpoints using `pytest` and `httpx`.
*   **Load tests** for scoring endpoint under high candidate volume.

## 10. Deployment & Monitoring

*   **Dockerize** the FastAPI application and run on localhost.

## 11. How Cursor Helps

*   **Rapid code scaffolding** for FastAPI routes and Pydantic models.
*   **Auto-completion** of SQLAlchemy queries and JSON schema definitions.
*   **Assistance in prompt engineering** for the LLM service.
*   **Suggestion of best practices** for parsing and validating LLM outputs.
*   **Visualization snippets** for D3.js payload formatting.
