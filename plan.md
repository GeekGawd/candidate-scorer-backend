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
|  Endpoints     |      |  Layer              |      |  (PostgreSQL)    |
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

| Method | Endpoint                             | Description                                            |
| ------ | ------------------------------------ | ------------------------------------------------------ |
| POST   | `/config/generate`                   | Generates a `config_json` from a natural text description |
| GET    | `/config/{role}`                     | Retrieve scoring configuration for a role              |
| PUT    | `/config/{role}`                     | Update scoring configuration                           |
| POST   | `/score/{role}`                      | Submit candidate data, return raw scores               |
| GET    | `/rank/{role}`                       | Return ranked list of candidates              |
| GET    | `/rank/{role}/explain/{candidateId}` | Return detailed explanation for one candidate |
| GET    | `/metrics/bias`                      | Retrieve bias metrics and reports             |

## 5. Database Schema (PostgreSQL)

```sql
-- Roles & Configurations
CREATE TABLE role_config (
  role_id      SERIAL PRIMARY KEY,
  role_name    TEXT UNIQUE NOT NULL,
  config_json  JSONB NOT NULL,
  updated_at   TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Candidates
CREATE TABLE candidate (
  id           SERIAL PRIMARY KEY,
  profile_json JSONB NOT NULL,
  created_at   TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Scores
CREATE TABLE candidate_score (
  candidate_id INTEGER REFERENCES candidate(id),
  role_id      INTEGER REFERENCES role_config(role_id),
  raw_scores   JSONB,
  total_score  FLOAT,
  scored_at    TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  PRIMARY KEY (candidate_id, role_id)
);

-- Bias Metrics
CREATE TABLE bias_metric (
  metric_id    SERIAL PRIMARY KEY,
  role_id      INTEGER REFERENCES role_config(role_id),
  metric_name  TEXT,
  metric_value JSONB,
  recorded_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## 6. Scoring Algorithm Design

1.  **Load role configuration** and LLM scoring rubric from `role_config.config_json`.
2.  **For each candidate**, prepare a detailed prompt including the role description, scoring rubric, and the candidate's profile data.
3.  **Invoke the `LLM Integration Service`** with the composed prompt.
4.  **The LLM will**:
    *   Analyze the provided materials.
    *   Generate a comprehensive evaluation as a structured JSON object, including:
        *   An overall suitability score (e.g., 1-100).
        *   A breakdown of scores for each key competency.
        *   A concise rationale for its assessment.
        *   Direct quotes or evidence from the profile to support its findings.
5.  **Receive and validate** the LLM's JSON response.
6.  **Store the detailed LLM output** (`raw_scores`) and the main score (`total_score`) in the `candidate_score` table.

## 7. Verification & Fairness Workflow

1.  **Job Description Analysis:** Before posting a new role, use the `Candidate Verification & Fairness Module` to scan the job description for biased language.
2.  **Candidate Verification:** When a candidate is submitted, automatically crawl their provided public profiles (e.g., GitHub, LinkedIn).
3.  **Information Synthesis:** Use an LLM to summarize the crawled data and cross-reference it with the resume, creating a "verification summary" that is attached to the candidate's profile. This summary is then used as an input for the scoring algorithm.
4.  **Scheduled Audits:** Run a periodic job to analyze aggregate scoring data for statistical disparities.
5.  **Alerting & Logging:** Alert HR or hiring managers of significant bias metrics and log all actions for transparency.

## 8. Explanation & Visualization

*   **Explanation Endpoint** `/rank/{role}/explain/{candidateId}`:

  * Return JSON with breakdown: skills, weights, experience impact.
*   **Visualization Payload**:

  * Chart-ready data arrays for front-end bar and radar charts.

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
