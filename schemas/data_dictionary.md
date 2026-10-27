# Data Dictionary: Recruitment Management & Workflow Validation System

## Overview
This document specifies the database tables, fields, data types, constraints, nullability, default values, and business descriptions for the Recruitment Management System. The database uses MySQL 8.0+ with InnoDB storage engine and `utf8mb4` encoding. All timestamps are standardized to UTC.

---

### 1. `departments`
Stores organizational department units.

| Column | Type | Nullable | Key / Constraint | Description |
|---|---|---|---|---|
| `id` | `INT` | NO | PK, AUTO_INCREMENT | Synthetic internal surrogate key |
| `code` | `VARCHAR(50)` | NO | UNIQUE | Unique department identifier code (e.g., `ENG`, `HR`, `FIN`) |
| `name` | `VARCHAR(100)` | NO | | Human-readable name of the department |
| `cost_center` | `VARCHAR(50)` | NO | | Cost center code for accounting |
| `created_at` | `DATETIME` | NO | UTC | Row creation timestamp |
| `updated_at` | `DATETIME` | NO | UTC | Row modification timestamp |

---

### 2. `job_requisitions`
Manages open headcounts, requirements, salary bands, and requisition lifecycles.

| Column | Type | Nullable | Key / Constraint | Description |
|---|---|---|---|---|
| `requisition_id` | `VARCHAR(50)` | NO | PK | Deterministic ID format: `REQ-YYYY-NNNNNN` |
| `title` | `VARCHAR(150)` | NO | INDEX | Job posting title |
| `department_id` | `INT` | NO | FK (`departments.id`) | Foreign key to owning department |
| `hiring_manager_id` | `VARCHAR(50)` | NO | | Employee ID of the hiring manager |
| `status` | `ENUM` | NO | INDEX | `DRAFT`, `PENDING_APPROVAL`, `OPEN`, `FILLED`, `CLOSED`, `CANCELLED` |
| `headcount` | `INT` | NO | DEFAULT 1 | Target number of hires |
| `min_experience_years`| `FLOAT` | NO | DEFAULT 0.0 | Minimum required years of industry experience |
| `min_salary` | `FLOAT` | NO | CHECK (>= 0) | Lower boundary of salary band |
| `max_salary` | `FLOAT` | NO | CHECK (>= min_salary)| Upper boundary of salary band |
| `currency` | `VARCHAR(10)` | NO | DEFAULT 'USD' | Currency code |
| `location` | `VARCHAR(100)` | NO | DEFAULT 'Remote' | Job location / work modality |
| `opened_at` | `DATETIME` | YES | | Timestamp when role was formally opened |
| `closed_at` | `DATETIME` | YES | | Timestamp when role was closed or filled |
| `created_at` | `DATETIME` | NO | UTC | Creation timestamp |
| `updated_at` | `DATETIME` | NO | UTC | Last update timestamp |

---

### 3. `candidates`
Stores candidate profile data. Strictly excludes age, gender, caste, religion, disability, or other demographic attributes.

| Column | Type | Nullable | Key / Constraint | Description |
|---|---|---|---|---|
| `candidate_id` | `VARCHAR(50)` | NO | PK | Deterministic ID format: `CAND-NNNNNN` |
| `first_name` | `VARCHAR(100)` | NO | | Candidate first name |
| `last_name` | `VARCHAR(100)` | NO | | Candidate last name |
| `email` | `VARCHAR(150)` | NO | UNIQUE, INDEX | Candidate email address |
| `phone` | `VARCHAR(50)` | NO | | Candidate telephone contact |
| `location` | `VARCHAR(100)` | NO | | Candidate location |
| `total_experience_years` | `FLOAT` | NO | DEFAULT 0.0 | Cumulative professional experience |
| `created_at` | `DATETIME` | NO | UTC | Profile creation timestamp |
| `updated_at` | `DATETIME` | NO | UTC | Profile update timestamp |

---

### 4. `applications`
Connects a candidate to a specific job requisition and tracks progress through hiring stages.

| Column | Type | Nullable | Key / Constraint | Description |
|---|---|---|---|---|
| `application_id` | `VARCHAR(120)` | NO | PK | Format: `APP-<requisition-id>-<candidate-id>` |
| `candidate_id` | `VARCHAR(50)` | NO | FK (`candidates.candidate_id`) | Referenced candidate |
| `requisition_id` | `VARCHAR(50)` | NO | FK (`job_requisitions.requisition_id`)| Referenced requisition |
| `current_stage` | `ENUM` | NO | INDEX | `APPLIED`, `SCREENING`, `INTERVIEW`, `DECISION_PENDING`, `OFFER_PENDING_APPROVAL`, `OFFERED`, `ACCEPTED`, `REJECTED`, `WITHDRAWN`, `OFFER_REJECTED`, `OFFER_EXPIRED` |
| `applied_at` | `DATETIME` | NO | UTC | Timestamp when application was lodged |
| `updated_at` | `DATETIME` | NO | UTC | Timestamp of last stage update |
| `screening_score` | `FLOAT` | YES | | Derived weighted score (0–100) |
| `decision_reason` | `VARCHAR(255)` | YES | | Reason description for state progression or exit |

---

### 5. `resume_artifacts`
Metadata and parsed skill summaries extracted from synthetic candidate resumes.

| Column | Type | Nullable | Key / Constraint | Description |
|---|---|---|---|---|
| `artifact_id` | `INT` | NO | PK, AUTO_INCREMENT | Surrogate key |
| `candidate_id` | `VARCHAR(50)` | NO | FK (`candidates.candidate_id`) | Candidate owner |
| `file_name` | `VARCHAR(200)` | NO | | Simulated filename |
| `file_hash` | `VARCHAR(64)` | NO | SHA-256 | Cryptographic SHA-256 digest |
| `resume_text_summary` | `TEXT` | NO | | Extracted text summary |
| `parsed_skills_json` | `TEXT` | NO | | JSON list of extracted skill keywords |
| `education_level` | `VARCHAR(50)` | NO | | Degree level (e.g., Bachelor, Master, PhD) |
| `years_experience`| `FLOAT` | NO | | Extracted years of experience |
| `created_at` | `DATETIME` | NO | UTC | Record creation timestamp |

---

### 6. `skills`
Master catalog of technical, managerial, and domain competencies.

| Column | Type | Nullable | Key / Constraint | Description |
|---|---|---|---|---|
| `skill_id` | `INT` | NO | PK, AUTO_INCREMENT | Surrogate primary key |
| `name` | `VARCHAR(100)` | NO | UNIQUE, INDEX | Canonical skill name (e.g. `Python`, `Docker`, `SQL`) |
| `category` | `VARCHAR(50)` | NO | | Skill category (e.g., `Backend`, `Database`, `DevOps`) |
| `created_at` | `DATETIME` | NO | UTC | Master entry creation timestamp |

---

### 7. `candidate_skills`
Bridge table associating candidates with validated skill proficiencies.

| Column | Type | Nullable | Key / Constraint | Description |
|---|---|---|---|---|
| `id` | `INT` | NO | PK, AUTO_INCREMENT | Bridge surrogate key |
| `candidate_id` | `VARCHAR(50)` | NO | FK (`candidates.candidate_id`) | Associated candidate |
| `skill_id` | `INT` | NO | FK (`skills.skill_id`) | Associated skill |
| `proficiency_level` | `INT` | NO | CHECK (1..5) | Numeric proficiency rating (1=Novice, 5=Expert) |
| `years_experience` | `FLOAT` | NO | DEFAULT 1.0 | Years practical experience in this skill |

---

### 8. `requisition_required_skills`
Bridge table associating job requisitions with required and preferred qualifications.

| Column | Type | Nullable | Key / Constraint | Description |
|---|---|---|---|---|
| `id` | `INT` | NO | PK, AUTO_INCREMENT | Bridge surrogate key |
| `requisition_id` | `VARCHAR(50)` | NO | FK (`job_requisitions.requisition_id`)| Associated job requisition |
| `skill_id` | `INT` | NO | FK (`skills.skill_id`) | Associated skill |
| `is_required` | `BOOLEAN` | NO | DEFAULT TRUE | True if prerequisite, False if preferred |
| `min_experience_years`| `FLOAT` | NO | DEFAULT 1.0 | Minimum threshold years required |

---

### 9. `screening_rules`
Defines configurable, explainable evaluation criteria per requisition.

| Column | Type | Nullable | Key / Constraint | Description |
|---|---|---|---|---|
| `rule_id` | `INT` | NO | PK, AUTO_INCREMENT | Surrogate primary key |
| `requisition_id` | `VARCHAR(50)` | NO | FK (`job_requisitions.requisition_id`)| Associated requisition |
| `rule_version` | `VARCHAR(20)` | NO | DEFAULT '1.0' | Version tag for historical auditability |
| `skill_weight` | `FLOAT` | NO | DEFAULT 0.60 | Weight allocated to skills match (0.0..1.0) |
| `experience_weight` | `FLOAT` | NO | DEFAULT 0.25 | Weight allocated to experience match (0.0..1.0) |
| `assessment_weight` | `FLOAT` | NO | DEFAULT 0.15 | Weight allocated to assessment score (0.0..1.0) |
| `passing_threshold` | `FLOAT` | NO | DEFAULT 70.0 | Minimum score to advance to interview stage |
| `is_active` | `BOOLEAN` | NO | DEFAULT TRUE | Active flag |
| `created_at` | `DATETIME` | NO | UTC | Rule creation timestamp |

---

### 10. `candidate_screening_results`
Stores the exact calculation breakdown and explainable decision for every application screened.

| Column | Type | Nullable | Key / Constraint | Description |
|---|---|---|---|---|
| `id` | `INT` | NO | PK, AUTO_INCREMENT | Surrogate key |
| `application_id` | `VARCHAR(120)` | NO | FK (`applications.application_id`) | Screened application |
| `rule_version` | `VARCHAR(20)` | NO | | Version of rule utilized |
| `skill_match_score` | `FLOAT` | NO | 0–100 | Normalized skill match component |
| `experience_score` | `FLOAT` | NO | 0–100 | Normalized experience component |
| `assessment_score` | `FLOAT` | NO | 0–100 | Normalized assessment component |
| `final_score` | `FLOAT` | NO | 0–100 | Total weighted score |
| `threshold` | `FLOAT` | NO | | Cutoff threshold used |
| `decision` | `VARCHAR(20)` | NO | `PASS` / `FAIL` | Screening outcome |
| `reason_codes_json` | `TEXT` | NO | JSON array | Machine-readable explanation tags |
| `evaluated_at` | `DATETIME` | NO | UTC | Timestamp of screening execution |

---

### 11. `interviewers`
Employees authorized to conduct interviews.

| Column | Type | Nullable | Key / Constraint | Description |
|---|---|---|---|---|
| `interviewer_id` | `VARCHAR(50)` | NO | PK | Format: `EMP-NNNNNN` |
| `name` | `VARCHAR(100)` | NO | | Full name |
| `email` | `VARCHAR(150)` | NO | UNIQUE | Corporate email address |
| `department_id` | `INT` | NO | FK (`departments.id`) | Home department |
| `title` | `VARCHAR(100)` | NO | | Job title |
| `is_active` | `BOOLEAN` | NO | DEFAULT TRUE | Active availability flag |
| `created_at` | `DATETIME` | NO | UTC | Registration timestamp |

---

### 12. `interviews`
Scheduled interview sessions.

| Column | Type | Nullable | Key / Constraint | Description |
|---|---|---|---|---|
| `interview_id` | `VARCHAR(50)` | NO | PK | Deterministic format: `INT-YYYY-NNNNNN` |
| `application_id` | `VARCHAR(120)` | NO | FK (`applications.application_id`) | Associated candidate application |
| `round_number` | `INT` | NO | DEFAULT 1 | Sequential round number (1, 2, 3...) |
| `round_type` | `ENUM` | NO | | `HR`, `TECHNICAL`, `SYSTEM_DESIGN`, `BEHAVIORAL`, `EXECUTIVE` |
| `scheduled_start` | `DATETIME` | NO | INDEX | Start date and time in UTC |
| `scheduled_end` | `DATETIME` | NO | INDEX, CHECK (> start)| End date and time in UTC |
| `status` | `ENUM` | NO | INDEX | `SCHEDULED`, `COMPLETED`, `CANCELLED`, `RESCHEDULED` |
| `created_at` | `DATETIME` | NO | UTC | Booking timestamp |
| `updated_at` | `DATETIME` | NO | UTC | Rescheduling/status update timestamp |

---

### 13. `interviewer_assignments`
Bridge enabling multiple interviewers per interview round.

| Column | Type | Nullable | Key / Constraint | Description |
|---|---|---|---|---|
| `id` | `INT` | NO | PK, AUTO_INCREMENT | Bridge surrogate key |
| `interview_id` | `VARCHAR(50)` | NO | FK (`interviews.interview_id`) | Assigned interview |
| `interviewer_id` | `VARCHAR(50)` | NO | FK (`interviewers.interviewer_id`) | Assigned interviewer |
| `assigned_at` | `DATETIME` | NO | UTC | Assignment timestamp |

---

### 14. `feedback`
Structured evaluation submitted by an interviewer for a completed round.

| Column | Type | Nullable | Key / Constraint | Description |
|---|---|---|---|---|
| `feedback_id` | `VARCHAR(120)` | NO | PK | Deterministic: `FB-<interview-id>-<interviewer-id>` |
| `interview_id` | `VARCHAR(50)` | NO | FK (`interviews.interview_id`) | Interview evaluated |
| `interviewer_id` | `VARCHAR(50)` | NO | FK (`interviewers.interviewer_id`) | Submitting interviewer |
| `technical_rating` | `INT` | NO | CHECK (1..5) | Technical competence score |
| `communication_rating`| `INT`| NO | CHECK (1..5) | Communication and articulation |
| `problem_solving_rating`|`INT`| NO | CHECK (1..5) | Analytical and problem solving ability |
| `overall_score` | `FLOAT` | NO | CHECK (1.0..5.0) | Weighted composite round score |
| `recommendation` | `ENUM` | NO | | `STRONG_HIRE`, `HIRE`, `NO_HIRE`, `STRONG_NO_HIRE` |
| `notes` | `TEXT` | NO | | Mandatory qualitative feedback justification |
| `version` | `INT` | NO | DEFAULT 1 | Version counter for edits |
| `submitted_at` | `DATETIME` | NO | UTC | Initial submission timestamp |
| `updated_at` | `DATETIME` | NO | UTC | Last modification timestamp |

---

### 15. `offers`
Formal job offers extended to successful candidates.

| Column | Type | Nullable | Key / Constraint | Description |
|---|---|---|---|---|
| `offer_id` | `VARCHAR(50)` | NO | PK | Deterministic format: `OFF-YYYY-NNNNNN` |
| `application_id` | `VARCHAR(120)` | NO | FK (`applications.application_id`) | Candidate application |
| `base_salary` | `FLOAT` | NO | CHECK (> 0) | Annual base compensation |
| `sign_on_bonus` | `FLOAT` | NO | DEFAULT 0.0 | One-time sign-on bonus |
| `equity_shares` | `INT` | NO | DEFAULT 0 | Stock option or RSU grant shares |
| `currency` | `VARCHAR(10)` | NO | DEFAULT 'USD' | Currency code |
| `status` | `ENUM` | NO | INDEX | `DRAFT`, `PENDING_APPROVAL`, `APPROVED`, `ISSUED`, `ACCEPTED`, `REJECTED`, `WITHDRAWN`, `EXPIRED` |
| `is_out_of_band` | `BOOLEAN` | NO | DEFAULT FALSE | True if salary > requisition max_salary |
| `exception_approved_by`|`VARCHAR(100)`| YES | | Authorized executive who approved band exception |
| `issued_at` | `DATETIME` | YES | | Official issue timestamp |
| `expires_at` | `DATETIME` | YES | | Deadline timestamp for candidate acceptance |
| `responded_at` | `DATETIME` | YES | | Candidate reply timestamp |
| `created_at` | `DATETIME` | NO | UTC | Draft creation timestamp |
| `updated_at` | `DATETIME` | NO | UTC | Status update timestamp |

---

### 16. `requisition_approvals` & `offer_approvals`
Audit approval chains for requisition openings and offer issuance.

| Column | Type | Nullable | Key / Constraint | Description |
|---|---|---|---|---|
| `approval_id` | `INT` | NO | PK, AUTO_INCREMENT | Surrogate key |
| `requisition_id` / `offer_id` | `VARCHAR(50)` | NO | FK | Target entity ID |
| `approver_id` | `VARCHAR(50)` | NO | | Approving executive/manager ID |
| `status` | `ENUM` | NO | DEFAULT 'PENDING' | `PENDING`, `APPROVED`, `REJECTED` |
| `comments` | `VARCHAR(255)` | YES | | Approval remarks or condition codes |
| `decided_at` | `DATETIME` | YES | | Timestamp of approval decision |
| `created_at` | `DATETIME` | NO | UTC | Request timestamp |

---

### 17. `application_events` & `audit_events`
Append-only immutable event streams for lifecycle state changes and data modifications.

| Table | Column | Type | Description |
|---|---|---|---|
| `application_events` | `event_id` | `INT PK` | Auto-increment event ID |
| `application_events` | `application_id` | `VARCHAR(120) FK` | Application transitioning |
| `application_events` | `from_stage` | `VARCHAR(50)` | Source lifecycle state |
| `application_events` | `to_stage` | `VARCHAR(50)` | Target lifecycle state |
| `application_events` | `actor` | `VARCHAR(100)` | User or automated service initiating change |
| `application_events` | `reason` | `VARCHAR(255)` | Business justification |
| `application_events` | `rule_version` | `VARCHAR(20)` | Active rule version applied |
| `application_events` | `event_timestamp` | `DATETIME` | UTC timestamp of event |
| `audit_events` | `audit_id` | `INT PK` | Auto-increment ledger sequence |
| `audit_events` | `entity_type` | `VARCHAR(50)` | Target table/domain entity |
| `audit_events` | `entity_id` | `VARCHAR(120)` | Target entity primary key |
| `audit_events` | `action` | `VARCHAR(50)` | `CREATE`, `UPDATE`, `TRANSITION`, `DELETE` |
| `audit_events` | `previous_state_json` | `TEXT` | Pre-change JSON snapshot |
| `audit_events` | `new_state_json` | `TEXT` | Post-change JSON snapshot |
| `audit_events` | `actor` | `VARCHAR(100)` | Initiator identifier |
| `audit_events` | `timestamp` | `DATETIME` | UTC event time |
| `audit_events` | `reason` | `VARCHAR(255)` | Contextual explanation |

---

### 18. `anomaly_records`
Captures all blocked or detected violations across the five mandatory scenarios.

| Column | Type | Nullable | Key / Constraint | Description |
|---|---|---|---|---|
| `issue_id` | `VARCHAR(50)` | NO | PK | Deterministic issue ID (e.g. `ANOM-2026-000001`) |
| `issue_type` | `VARCHAR(50)` | NO | INDEX | Anomaly category |
| `affected_entity_type` | `VARCHAR(50)` | NO | | Entity type (`INTERVIEW`, `APPLICATION`, `OFFER`, `REQUISITION`) |
| `affected_record_id` | `VARCHAR(120)` | NO | | Target record key |
| `expected_decision` | `VARCHAR(100)` | NO | | Policy mandated decision |
| `severity` | `ENUM` | NO | | `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` |
| `detection_result` | `ENUM` | NO | | `BLOCKED_BY_VALIDATION` vs `DETECTED_IN_AUDIT` |
| `explanation` | `TEXT` | NO | | Detailed violation summary |
| `recommended_action` | `TEXT` | NO | | Remediating procedure for operations team |
| `detected_at` | `DATETIME` | NO | UTC | Timestamp when anomaly was flagged |
