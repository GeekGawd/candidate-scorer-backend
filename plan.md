# Candidate Ranking System Plan

## 1. Introduction

This document outlines a step-by-step plan to implement a Candidate Ranking System in a FastAPI backend. The system will provide:

* Objective, data-driven candidate evaluation
* Configurable scoring criteria and weighting
* Experience level assessment relative to role seniority
* Bias detection and mitigation
* Ranking visualization and explanation

## 2. Architecture Overview

```
+----------------+      +---------------+      +------------------+
|  FastAPI REST  | <--> |  Business     | <--> |  Database        |
|  Endpoints     |      |  Logic Layer  |      |  (PostgreSQL)    |
+----------------+      +---------------+      +------------------+
        |                       |
        v                       v
+----------------+      +------------------+
|  Scoring       |      |  Bias Mitigation|
|  Engine        |      |  & Monitoring    |
+----------------+      +------------------+
        |                       |
        v                       v
+----------------+      +------------------+
|  Config Service|      |  Explanation     |
+----------------+      |  & Visualization |
                        +------------------+
```

## 3. Components & Modules

### 3.1 Scoring Engine

* **Inputs:** Candidate profile, role-specific requirements, skill weights
* **Outputs:** Raw scores per criterion, aggregate score
* **Features:**

  * Weighted sum of must-have vs. nice-to-have skills
  * Experience multiplier based on seniority level
  * Normalization of scores

### 3.2 Configurable Criteria Service

* Expose JSON/YAML configs defining:

  * Must-have skills and their weights
  * Nice-to-have skills and their weights
  * Experience thresholds per role
* Endpoint to retrieve and update configurations

### 3.3 Bias Detection & Mitigation Module

* Analyze score distribution across demographics (e.g., gender, ethnicity)
* Implement statistical checks (e.g., disparate impact ratio)
* Apply corrective adjustments or flag anomalies
* Log metrics for monitoring

### 3.4 Explanation & Visualization Service

* Generate human-readable explanations for each candidate’s rank:

  * Breakdown of scores by criterion
  * Highlight areas of strength and weakness
* Provide data for front-end charts (e.g., JSON payloads for D3.js)

## 4. API Design

| Method | Endpoint                             | Description                                   |
| ------ | ------------------------------------ | --------------------------------------------- |
| GET    | `/config/{role}`                     | Retrieve scoring configuration for a role     |
| PUT    | `/config/{role}`                     | Update scoring configuration                  |
| POST   | `/score/{role}`                      | Submit candidate data, return raw scores      |
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

1. **Load role configuration** from `role_config.config_json`.
2. **Extract candidate skills** and experience details.
3. **Compute individual scores**:

   * For each must-have skill: assign full weight if present, zero otherwise.
   * For each nice-to-have skill: partial weight based on proficiency level.
4. **Apply experience multiplier**:

   * Map years of experience to a multiplier (e.g., 1.0 for mid, 1.2 for senior).
5. **Normalize total score** to a 0–100 scale.
6. **Store raw\_scores and total\_score** in `candidate_score`.

## 7. Bias Detection & Mitigation Workflow

* **Schedule** a daily job to compute bias metrics via `/metrics/bias`.
* **Detect** disparities using statistical tests (e.g., 4/5ths rule).
* **Mitigate** by adjusting candidate scores or alerting HR for manual review.
* **Log** metrics in `bias_metric` table for audit.

## 8. Explanation & Visualization

* **Explanation Endpoint** `/rank/{role}/explain/{candidateId}`:

  * Return JSON with breakdown: skills, weights, experience impact.
* **Visualization Payload**:

  * Chart-ready data arrays for front-end bar and radar charts.

## 9. Testing Strategy

* **Unit tests** for scoring functions, config parsing, bias checks.
* **Integration tests** for API endpoints using `pytest` and `httpx`.
* **Load tests** for scoring endpoint under high candidate volume.

## 10. Deployment & Monitoring

* **Dockerize** the FastAPI application.
* Use **GitHub Actions** for CI/CD: linting, tests, container build.
* Deploy to **Kubernetes** / **AWS ECS Fargate**.
* Monitor with **Prometheus** (collect latency, error rates) and **Grafana** dashboards.

## 11. How Cursor Helps

* **Rapid code scaffolding** for FastAPI routes and Pydantic models.
* **Auto-completion** of SQLAlchemy queries and JSON schema definitions.
* **Suggestion of best practices** for bias detection algorithms.
* **Visualization snippets** for D3.js payload formatting.
