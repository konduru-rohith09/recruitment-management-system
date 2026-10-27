# Entity Relationships and Architecture

## 1. Architectural Relationship Matrix

```mermaid
erDiagram
    Department ||--o{ JobRequisition : "has requisitions (1:N)"
    Department ||--o{ Interviewer : "employs (1:N)"
    JobRequisition ||--o{ Application : "receives (1:N)"
    JobRequisition ||--o{ ScreeningRule : "defines (1:N)"
    JobRequisition ||--o{ RequisitionRequiredSkill : "requires (1:N)"
    JobRequisition ||--o{ RequisitionApproval : "subject to (1:N)"
    
    Candidate ||--o{ Application : "submits (1:N)"
    Candidate ||--o{ ResumeArtifact : "owns (1:N)"
    Candidate ||--o{ CandidateSkill : "possesses (1:N)"
    
    Skill ||--o{ CandidateSkill : "mapped to (1:N)"
    Skill ||--o{ RequisitionRequiredSkill : "referenced in (1:N)"
    
    Application ||--o{ Interview : "progresses to (1:N)"
    Application ||--o{ Offer : "qualifies for (1:N)"
    Application ||--o{ ApplicationEvent : "tracks lifecycle (1:N)"
    Application ||--o{ CandidateScreeningResult : "evaluated by (1:N)"
    
    Interview ||--o{ InterviewerAssignment : "assigns (1:N)"
    Interviewer ||--o{ InterviewerAssignment : "attends (1:N)"
    Interview ||--o{ Feedback : "receives (1:N)"
    Interviewer ||--o{ Feedback : "submits (1:N)"
    
    Offer ||--o{ OfferApproval : "authorized by (1:N)"
```

---

## 2. Cardinality and Foreign Key Specification

### A. One-to-Many Relationships (1:N)
1. **`Department` -> `JobRequisition`**
   - Foreign Key: `job_requisitions.department_id` references `departments.id`
   - Delete rule: `RESTRICT` (A department cannot be deleted if active requisitions exist).
2. **`Department` -> `Interviewer`**
   - Foreign Key: `interviewers.department_id` references `departments.id`
   - Delete rule: `RESTRICT`.
3. **`JobRequisition` -> `Application`**
   - Foreign Key: `applications.requisition_id` references `job_requisitions.requisition_id`
   - Delete rule: `RESTRICT`.
4. **`Candidate` -> `Application`**
   - Foreign Key: `applications.candidate_id` references `candidates.candidate_id`
   - Delete rule: `RESTRICT`.
5. **`Candidate` -> `ResumeArtifact`**
   - Foreign Key: `resume_artifacts.candidate_id` references `candidates.candidate_id`
   - Delete rule: `CASCADE`.
6. **`JobRequisition` -> `ScreeningRule`**
   - Foreign Key: `screening_rules.requisition_id` references `job_requisitions.requisition_id`
   - Delete rule: `CASCADE`.
7. **`Application` -> `CandidateScreeningResult`**
   - Foreign Key: `candidate_screening_results.application_id` references `applications.application_id`
   - Delete rule: `CASCADE`.
8. **`Application` -> `Interview`**
   - Foreign Key: `interviews.application_id` references `applications.application_id`
   - Delete rule: `CASCADE`.
9. **`Interview` -> `Feedback`**
   - Foreign Key: `feedback.interview_id` references `interviews.interview_id`
   - Delete rule: `CASCADE`.
10. **`Interviewer` -> `Feedback`**
    - Foreign Key: `feedback.interviewer_id` references `interviewers.interviewer_id`
    - Delete rule: `RESTRICT`.
11. **`Application` -> `Offer`**
    - Foreign Key: `offers.application_id` references `applications.application_id`
    - Delete rule: `CASCADE`.
12. **`Offer` -> `OfferApproval`**
    - Foreign Key: `offer_approvals.offer_id` references `offers.offer_id`
    - Delete rule: `CASCADE`.
13. **`Application` -> `ApplicationEvent`**
    - Foreign Key: `application_events.application_id` references `applications.application_id`
    - Delete rule: `CASCADE`.

---

### B. Many-to-Many Relationships (N:M) Supported by Bridge Tables

1. **`Candidate` <-> `Skill`**
   - Bridge Table: `candidate_skills`
   - Attributes: `proficiency_level` (1..5), `years_experience`
   - Unique Constraint: `(candidate_id, skill_id)`
2. **`JobRequisition` <-> `Skill`**
   - Bridge Table: `requisition_required_skills`
   - Attributes: `is_required` (Boolean), `min_experience_years`
   - Unique Constraint: `(requisition_id, skill_id)`
3. **`Interview` <-> `Interviewer`**
   - Bridge Table: `interviewer_assignments`
   - Attributes: `assigned_at`
   - Unique Constraint: `(interview_id, interviewer_id)`
   - Allows panels with multiple interviewers per round and checks for conflicting bookings.

---

## 3. State Transition Matrix (Application Lifecycle)

```mermaid
stateDiagram-v2
    [*] --> APPLIED
    APPLIED --> SCREENING : Start Screening
    APPLIED --> WITHDRAWN : Candidate Withdrew
    
    SCREENING --> INTERVIEW : Score >= Threshold
    SCREENING --> REJECTED : Score < Threshold
    SCREENING --> WITHDRAWN : Candidate Withdrew
    
    INTERVIEW --> DECISION_PENDING : All Feedback Submitted
    INTERVIEW --> REJECTED : Disqualified
    INTERVIEW --> WITHDRAWN : Candidate Withdrew
    
    DECISION_PENDING --> OFFER_PENDING_APPROVAL : Positive Recommendation
    DECISION_PENDING --> REJECTED : Negative Recommendation
    DECISION_PENDING --> WITHDRAWN : Candidate Withdrew
    
    OFFER_PENDING_APPROVAL --> OFFERED : Approvals Completed
    OFFER_PENDING_APPROVAL --> REJECTED : Approvals Denied
    OFFER_PENDING_APPROVAL --> WITHDRAWN : Candidate Withdrew
    
    OFFERED --> ACCEPTED : Candidate Accepted
    OFFERED --> OFFER_REJECTED : Candidate Declined
    OFFERED --> OFFER_EXPIRED : Deadline Passed
    OFFERED --> WITHDRAWN : Role Cancelled/Withdrawn
    
    ACCEPTED --> [*]
    REJECTED --> [*]
    WITHDRAWN --> [*]
    OFFER_REJECTED --> [*]
    OFFER_EXPIRED --> [*]
```

### Transition Enforcement Rules:
1. **Screening to Interview**: Requires an active screening rule and an evaluated score meeting or exceeding `passing_threshold`.
2. **Interview to Decision Pending**: Requires every assigned interviewer on all scheduled interview rounds to submit completed `feedback`. Missing feedback blocks transition.
3. **Decision Pending to Offer Pending Approval**: Requires average feedback rating >= 3.0 and at least one positive recommendation (`HIRE` or `STRONG_HIRE`) with no `STRONG_NO_HIRE`.
4. **Offer Pending Approval to Offered**: Requires explicit `APPROVED` status in `offer_approvals`. If out-of-band salary is detected, `exception_approved_by` must be populated.
5. **Requisition Status Coherence**: An offer cannot be extended or an application advanced on a `CLOSED` or `CANCELLED` requisition.
