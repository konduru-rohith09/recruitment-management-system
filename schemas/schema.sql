-- Recruitment Management & Workflow Validation System
-- MySQL 8.0+ Schema Definition with InnoDB and utf8mb4

SET FOREIGN_KEY_CHECKS = 0;

-- 1. Departments
CREATE TABLE IF NOT EXISTS departments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    cost_center VARCHAR(50) NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    INDEX idx_dept_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Job Requisitions
CREATE TABLE IF NOT EXISTS job_requisitions (
    requisition_id VARCHAR(50) PRIMARY KEY,
    title VARCHAR(150) NOT NULL,
    department_id INT NOT NULL,
    hiring_manager_id VARCHAR(50) NOT NULL,
    status ENUM('DRAFT', 'PENDING_APPROVAL', 'OPEN', 'FILLED', 'CLOSED', 'CANCELLED') NOT NULL DEFAULT 'DRAFT',
    headcount INT NOT NULL DEFAULT 1,
    min_experience_years FLOAT NOT NULL DEFAULT 0.0,
    min_salary FLOAT NOT NULL,
    max_salary FLOAT NOT NULL,
    currency VARCHAR(10) NOT NULL DEFAULT 'USD',
    location VARCHAR(100) NOT NULL DEFAULT 'Remote',
    opened_at DATETIME NULL,
    closed_at DATETIME NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    CONSTRAINT fk_req_department FOREIGN KEY (department_id) REFERENCES departments (id) ON DELETE RESTRICT,
    CONSTRAINT check_salary_band_validity CHECK (min_salary >= 0 AND max_salary >= min_salary),
    INDEX idx_req_status (status),
    INDEX idx_req_department (department_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Candidates (Protected characteristics strictly omitted)
CREATE TABLE IF NOT EXISTS candidates (
    candidate_id VARCHAR(50) PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    phone VARCHAR(50) NOT NULL,
    location VARCHAR(100) NOT NULL,
    total_experience_years FLOAT NOT NULL DEFAULT 0.0,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    INDEX idx_cand_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Applications
CREATE TABLE IF NOT EXISTS applications (
    application_id VARCHAR(120) PRIMARY KEY,
    candidate_id VARCHAR(50) NOT NULL,
    requisition_id VARCHAR(50) NOT NULL,
    current_stage ENUM('APPLIED', 'SCREENING', 'INTERVIEW', 'DECISION_PENDING', 'OFFER_PENDING_APPROVAL', 'OFFERED', 'ACCEPTED', 'REJECTED', 'WITHDRAWN', 'OFFER_REJECTED', 'OFFER_EXPIRED') NOT NULL DEFAULT 'APPLIED',
    applied_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    screening_score FLOAT NULL,
    decision_reason VARCHAR(255) NULL,
    CONSTRAINT fk_app_candidate FOREIGN KEY (candidate_id) REFERENCES candidates (candidate_id) ON DELETE RESTRICT,
    CONSTRAINT fk_app_requisition FOREIGN KEY (requisition_id) REFERENCES job_requisitions (requisition_id) ON DELETE RESTRICT,
    CONSTRAINT uq_req_candidate_baseline UNIQUE (requisition_id, candidate_id),
    INDEX idx_app_candidate (candidate_id),
    INDEX idx_app_requisition (requisition_id),
    INDEX idx_app_stage (current_stage)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. Resume Artifacts
CREATE TABLE IF NOT EXISTS resume_artifacts (
    artifact_id INT AUTO_INCREMENT PRIMARY KEY,
    candidate_id VARCHAR(50) NOT NULL,
    file_name VARCHAR(200) NOT NULL,
    file_hash VARCHAR(64) NOT NULL,
    resume_text_summary TEXT NOT NULL,
    parsed_skills_json TEXT NOT NULL,
    education_level VARCHAR(50) NOT NULL,
    years_experience FLOAT NOT NULL,
    created_at DATETIME NOT NULL,
    CONSTRAINT fk_resume_candidate FOREIGN KEY (candidate_id) REFERENCES candidates (candidate_id) ON DELETE CASCADE,
    INDEX idx_resume_cand (candidate_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. Skills
CREATE TABLE IF NOT EXISTS skills (
    skill_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    category VARCHAR(50) NOT NULL,
    created_at DATETIME NOT NULL,
    INDEX idx_skill_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. Candidate Skills (Bridge)
CREATE TABLE IF NOT EXISTS candidate_skills (
    id INT AUTO_INCREMENT PRIMARY KEY,
    candidate_id VARCHAR(50) NOT NULL,
    skill_id INT NOT NULL,
    proficiency_level INT NOT NULL DEFAULT 3,
    years_experience FLOAT NOT NULL DEFAULT 1.0,
    CONSTRAINT fk_cskill_candidate FOREIGN KEY (candidate_id) REFERENCES candidates (candidate_id) ON DELETE CASCADE,
    CONSTRAINT fk_cskill_skill FOREIGN KEY (skill_id) REFERENCES skills (skill_id) ON DELETE RESTRICT,
    CONSTRAINT uq_cand_skill UNIQUE (candidate_id, skill_id),
    CONSTRAINT check_proficiency_range CHECK (proficiency_level >= 1 AND proficiency_level <= 5),
    INDEX idx_cskill_cand (candidate_id),
    INDEX idx_cskill_skill (skill_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Supporting: Requisition Required Skills (Bridge)
CREATE TABLE IF NOT EXISTS requisition_required_skills (
    id INT AUTO_INCREMENT PRIMARY KEY,
    requisition_id VARCHAR(50) NOT NULL,
    skill_id INT NOT NULL,
    is_required BOOLEAN NOT NULL DEFAULT TRUE,
    min_experience_years FLOAT NOT NULL DEFAULT 1.0,
    CONSTRAINT fk_rskill_req FOREIGN KEY (requisition_id) REFERENCES job_requisitions (requisition_id) ON DELETE CASCADE,
    CONSTRAINT fk_rskill_skill FOREIGN KEY (skill_id) REFERENCES skills (skill_id) ON DELETE RESTRICT,
    CONSTRAINT uq_req_skill UNIQUE (requisition_id, skill_id),
    INDEX idx_rskill_req (requisition_id),
    INDEX idx_rskill_skill (skill_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8. Screening Rules
CREATE TABLE IF NOT EXISTS screening_rules (
    rule_id INT AUTO_INCREMENT PRIMARY KEY,
    requisition_id VARCHAR(50) NOT NULL,
    rule_version VARCHAR(20) NOT NULL DEFAULT '1.0',
    skill_weight FLOAT NOT NULL DEFAULT 0.60,
    experience_weight FLOAT NOT NULL DEFAULT 0.25,
    assessment_weight FLOAT NOT NULL DEFAULT 0.15,
    passing_threshold FLOAT NOT NULL DEFAULT 70.0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL,
    CONSTRAINT fk_rule_req FOREIGN KEY (requisition_id) REFERENCES job_requisitions (requisition_id) ON DELETE CASCADE,
    CONSTRAINT check_weights_non_neg CHECK (skill_weight >= 0 AND experience_weight >= 0 AND assessment_weight >= 0),
    CONSTRAINT check_threshold_range CHECK (passing_threshold >= 0 AND passing_threshold <= 100),
    INDEX idx_rule_req (requisition_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Supporting: Candidate Screening Results
CREATE TABLE IF NOT EXISTS candidate_screening_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    application_id VARCHAR(120) NOT NULL,
    rule_version VARCHAR(20) NOT NULL,
    skill_match_score FLOAT NOT NULL,
    experience_score FLOAT NOT NULL,
    assessment_score FLOAT NOT NULL,
    final_score FLOAT NOT NULL,
    threshold FLOAT NOT NULL,
    decision VARCHAR(20) NOT NULL,
    reason_codes_json TEXT NOT NULL,
    evaluated_at DATETIME NOT NULL,
    CONSTRAINT fk_sres_app FOREIGN KEY (application_id) REFERENCES applications (application_id) ON DELETE CASCADE,
    INDEX idx_sres_app (application_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 10. Interviewers
CREATE TABLE IF NOT EXISTS interviewers (
    interviewer_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    department_id INT NOT NULL,
    title VARCHAR(100) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL,
    CONSTRAINT fk_interviewer_dept FOREIGN KEY (department_id) REFERENCES departments (id) ON DELETE RESTRICT,
    INDEX idx_interviewer_dept (department_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 9. Interviews
CREATE TABLE IF NOT EXISTS interviews (
    interview_id VARCHAR(50) PRIMARY KEY,
    application_id VARCHAR(120) NOT NULL,
    round_number INT NOT NULL DEFAULT 1,
    round_type ENUM('HR', 'TECHNICAL', 'SYSTEM_DESIGN', 'BEHAVIORAL', 'EXECUTIVE') NOT NULL,
    scheduled_start DATETIME NOT NULL,
    scheduled_end DATETIME NOT NULL,
    status ENUM('SCHEDULED', 'COMPLETED', 'CANCELLED', 'RESCHEDULED') NOT NULL DEFAULT 'SCHEDULED',
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    CONSTRAINT fk_interview_app FOREIGN KEY (application_id) REFERENCES applications (application_id) ON DELETE CASCADE,
    CONSTRAINT check_interview_time_order CHECK (scheduled_end > scheduled_start),
    INDEX idx_int_app (application_id),
    INDEX idx_int_status (status),
    INDEX idx_int_start (scheduled_start),
    INDEX idx_int_end (scheduled_end)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Supporting: Interviewer Assignments (Bridge)
CREATE TABLE IF NOT EXISTS interviewer_assignments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    interview_id VARCHAR(50) NOT NULL,
    interviewer_id VARCHAR(50) NOT NULL,
    assigned_at DATETIME NOT NULL,
    CONSTRAINT fk_iassign_interview FOREIGN KEY (interview_id) REFERENCES interviews (interview_id) ON DELETE CASCADE,
    CONSTRAINT fk_iassign_interviewer FOREIGN KEY (interviewer_id) REFERENCES interviewers (interviewer_id) ON DELETE RESTRICT,
    CONSTRAINT uq_interview_interviewer UNIQUE (interview_id, interviewer_id),
    INDEX idx_iassign_int (interview_id),
    INDEX idx_iassign_emp (interviewer_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 11. Feedback
CREATE TABLE IF NOT EXISTS feedback (
    feedback_id VARCHAR(120) PRIMARY KEY,
    interview_id VARCHAR(50) NOT NULL,
    interviewer_id VARCHAR(50) NOT NULL,
    technical_rating INT NOT NULL,
    communication_rating INT NOT NULL,
    problem_solving_rating INT NOT NULL,
    overall_score FLOAT NOT NULL,
    recommendation ENUM('STRONG_HIRE', 'HIRE', 'NO_HIRE', 'STRONG_NO_HIRE') NOT NULL,
    notes TEXT NOT NULL,
    version INT NOT NULL DEFAULT 1,
    submitted_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    CONSTRAINT fk_fb_interview FOREIGN KEY (interview_id) REFERENCES interviews (interview_id) ON DELETE CASCADE,
    CONSTRAINT fk_fb_interviewer FOREIGN KEY (interviewer_id) REFERENCES interviewers (interviewer_id) ON DELETE RESTRICT,
    CONSTRAINT uq_feedback_per_interviewer UNIQUE (interview_id, interviewer_id),
    CONSTRAINT check_fb_tech_rating CHECK (technical_rating >= 1 AND technical_rating <= 5),
    CONSTRAINT check_fb_comm_rating CHECK (communication_rating >= 1 AND communication_rating <= 5),
    CONSTRAINT check_fb_prob_rating CHECK (problem_solving_rating >= 1 AND problem_solving_rating <= 5),
    CONSTRAINT check_fb_overall_score CHECK (overall_score >= 1.0 AND overall_score <= 5.0),
    INDEX idx_fb_interview (interview_id),
    INDEX idx_fb_interviewer (interviewer_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 12. Offers
CREATE TABLE IF NOT EXISTS offers (
    offer_id VARCHAR(50) PRIMARY KEY,
    application_id VARCHAR(120) NOT NULL,
    base_salary FLOAT NOT NULL,
    sign_on_bonus FLOAT NOT NULL DEFAULT 0.0,
    equity_shares INT NOT NULL DEFAULT 0,
    currency VARCHAR(10) NOT NULL DEFAULT 'USD',
    status ENUM('DRAFT', 'PENDING_APPROVAL', 'APPROVED', 'ISSUED', 'ACCEPTED', 'REJECTED', 'WITHDRAWN', 'EXPIRED') NOT NULL DEFAULT 'DRAFT',
    is_out_of_band BOOLEAN NOT NULL DEFAULT FALSE,
    exception_approved_by VARCHAR(100) NULL,
    issued_at DATETIME NULL,
    expires_at DATETIME NULL,
    responded_at DATETIME NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    CONSTRAINT fk_offer_app FOREIGN KEY (application_id) REFERENCES applications (application_id) ON DELETE CASCADE,
    CONSTRAINT check_base_salary_positive CHECK (base_salary > 0),
    INDEX idx_offer_app (application_id),
    INDEX idx_offer_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Supporting: Requisition Approvals
CREATE TABLE IF NOT EXISTS requisition_approvals (
    approval_id INT AUTO_INCREMENT PRIMARY KEY,
    requisition_id VARCHAR(50) NOT NULL,
    approver_id VARCHAR(50) NOT NULL,
    status ENUM('PENDING', 'APPROVED', 'REJECTED') NOT NULL DEFAULT 'PENDING',
    comments VARCHAR(255) NULL,
    decided_at DATETIME NULL,
    created_at DATETIME NOT NULL,
    CONSTRAINT fk_req_appr FOREIGN KEY (requisition_id) REFERENCES job_requisitions (requisition_id) ON DELETE CASCADE,
    INDEX idx_req_appr_req (requisition_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Supporting: Offer Approvals
CREATE TABLE IF NOT EXISTS offer_approvals (
    approval_id INT AUTO_INCREMENT PRIMARY KEY,
    offer_id VARCHAR(50) NOT NULL,
    approver_id VARCHAR(50) NOT NULL,
    status ENUM('PENDING', 'APPROVED', 'REJECTED') NOT NULL DEFAULT 'PENDING',
    comments VARCHAR(255) NULL,
    decided_at DATETIME NULL,
    created_at DATETIME NOT NULL,
    CONSTRAINT fk_offer_appr FOREIGN KEY (offer_id) REFERENCES offers (offer_id) ON DELETE CASCADE,
    INDEX idx_offer_appr_off (offer_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Supporting: Application Events (State Machine Ledger)
CREATE TABLE IF NOT EXISTS application_events (
    event_id INT AUTO_INCREMENT PRIMARY KEY,
    application_id VARCHAR(120) NOT NULL,
    from_stage VARCHAR(50) NOT NULL,
    to_stage VARCHAR(50) NOT NULL,
    actor VARCHAR(100) NOT NULL,
    reason VARCHAR(255) NOT NULL,
    rule_version VARCHAR(20) NOT NULL DEFAULT '1.0',
    event_timestamp DATETIME NOT NULL,
    CONSTRAINT fk_app_event_app FOREIGN KEY (application_id) REFERENCES applications (application_id) ON DELETE CASCADE,
    INDEX idx_app_event_app (application_id),
    INDEX idx_app_event_time (event_timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Supporting: Audit Events
CREATE TABLE IF NOT EXISTS audit_events (
    audit_id INT AUTO_INCREMENT PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(120) NOT NULL,
    action VARCHAR(50) NOT NULL,
    previous_state_json TEXT NULL,
    new_state_json TEXT NULL,
    actor VARCHAR(100) NOT NULL,
    timestamp DATETIME NOT NULL,
    reason VARCHAR(255) NULL,
    INDEX idx_audit_entity (entity_type, entity_id),
    INDEX idx_audit_time (timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Supporting: Anomaly Records
CREATE TABLE IF NOT EXISTS anomaly_records (
    issue_id VARCHAR(50) PRIMARY KEY,
    issue_type VARCHAR(50) NOT NULL,
    affected_entity_type VARCHAR(50) NOT NULL,
    affected_record_id VARCHAR(120) NOT NULL,
    expected_decision VARCHAR(100) NOT NULL,
    severity ENUM('LOW', 'MEDIUM', 'HIGH', 'CRITICAL') NOT NULL,
    detection_result ENUM('BLOCKED_BY_VALIDATION', 'DETECTED_IN_AUDIT') NOT NULL,
    explanation TEXT NOT NULL,
    recommended_action TEXT NOT NULL,
    detected_at DATETIME NOT NULL,
    INDEX idx_anom_type (issue_type),
    INDEX idx_anom_time (detected_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;
