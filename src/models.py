import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    Enum as SQLEnum,
    UniqueConstraint,
    CheckConstraint,
)
from sqlalchemy.orm import relationship

from src.database import Base


def utc_now() -> datetime:
    """Return the current UTC time as a naive datetime for SQLAlchemy columns."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


# Enums
class RequisitionStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    OPEN = "OPEN"
    FILLED = "FILLED"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class ApplicationStage(str, enum.Enum):
    APPLIED = "APPLIED"
    SCREENING = "SCREENING"
    INTERVIEW = "INTERVIEW"
    DECISION_PENDING = "DECISION_PENDING"
    OFFER_PENDING_APPROVAL = "OFFER_PENDING_APPROVAL"
    OFFERED = "OFFERED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    WITHDRAWN = "WITHDRAWN"
    OFFER_REJECTED = "OFFER_REJECTED"
    OFFER_EXPIRED = "OFFER_EXPIRED"


class RoundType(str, enum.Enum):
    HR = "HR"
    TECHNICAL = "TECHNICAL"
    SYSTEM_DESIGN = "SYSTEM_DESIGN"
    BEHAVIORAL = "BEHAVIORAL"
    EXECUTIVE = "EXECUTIVE"


class InterviewStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    RESCHEDULED = "RESCHEDULED"


class RecommendationEnum(str, enum.Enum):
    STRONG_HIRE = "STRONG_HIRE"
    HIRE = "HIRE"
    NO_HIRE = "NO_HIRE"
    STRONG_NO_HIRE = "STRONG_NO_HIRE"


class OfferStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    ISSUED = "ISSUED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    WITHDRAWN = "WITHDRAWN"
    EXPIRED = "EXPIRED"


class ApprovalStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class AnomalySeverity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AnomalyDetectionResult(str, enum.Enum):
    BLOCKED_BY_VALIDATION = "BLOCKED_BY_VALIDATION"
    DETECTED_IN_AUDIT = "DETECTED_IN_AUDIT"


# Core 1: Department
class Department(Base):
    __tablename__ = "departments"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    cost_center = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    requisitions = relationship(
        "JobRequisition",
        back_populates="department",
    )
    interviewers = relationship(
        "Interviewer",
        back_populates="department",
    )


# Core 2: Job Requisition
class JobRequisition(Base):
    __tablename__ = "job_requisitions"
    __table_args__ = (
        CheckConstraint(
            "min_salary >= 0 AND max_salary >= min_salary",
            name="check_salary_band_validity",
        ),
        {
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
        },
    )

    requisition_id = Column(String(50), primary_key=True)
    title = Column(String(150), nullable=False, index=True)
    department_id = Column(
        Integer,
        ForeignKey("departments.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    hiring_manager_id = Column(String(50), nullable=False)
    status = Column(
        SQLEnum(RequisitionStatus),
        default=RequisitionStatus.DRAFT,
        nullable=False,
        index=True,
    )
    headcount = Column(Integer, default=1, nullable=False)
    min_experience_years = Column(Float, default=0.0, nullable=False)
    min_salary = Column(Float, nullable=False)
    max_salary = Column(Float, nullable=False)
    currency = Column(String(10), default="USD", nullable=False)
    location = Column(String(100), default="Remote", nullable=False)
    opened_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    department = relationship("Department", back_populates="requisitions")
    applications = relationship("Application", back_populates="requisition")
    screening_rules = relationship(
        "ScreeningRule",
        back_populates="requisition",
    )
    required_skills = relationship(
        "RequisitionRequiredSkill",
        back_populates="requisition",
    )
    approvals = relationship(
        "RequisitionApproval",
        back_populates="requisition",
    )


# Core 3: Candidate
class Candidate(Base):
    __tablename__ = "candidates"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
    }

    candidate_id = Column(String(50), primary_key=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    phone = Column(String(50), nullable=False)
    location = Column(String(100), nullable=False)
    total_experience_years = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    applications = relationship("Application", back_populates="candidate")
    resume_artifacts = relationship(
        "ResumeArtifact",
        back_populates="candidate",
    )
    candidate_skills = relationship(
        "CandidateSkill",
        back_populates="candidate",
    )


# Core 4: Application
class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint(
            "requisition_id",
            "candidate_id",
            name="uq_req_candidate_baseline",
        ),
        {
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
        },
    )

    application_id = Column(String(120), primary_key=True)
    candidate_id = Column(
        String(50),
        ForeignKey("candidates.candidate_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    requisition_id = Column(
        String(50),
        ForeignKey("job_requisitions.requisition_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    current_stage = Column(
        SQLEnum(ApplicationStage),
        default=ApplicationStage.APPLIED,
        nullable=False,
        index=True,
    )
    applied_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )
    screening_score = Column(Float, nullable=True)
    decision_reason = Column(String(255), nullable=True)

    candidate = relationship("Candidate", back_populates="applications")
    requisition = relationship("JobRequisition", back_populates="applications")
    interviews = relationship("Interview", back_populates="application")
    offers = relationship("Offer", back_populates="application")
    events = relationship("ApplicationEvent", back_populates="application")
    screening_results = relationship(
        "CandidateScreeningResult",
        back_populates="application",
    )


# Core 5: ResumeArtifact
class ResumeArtifact(Base):
    __tablename__ = "resume_artifacts"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
    }

    artifact_id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(
        String(50),
        ForeignKey("candidates.candidate_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_name = Column(String(200), nullable=False)
    file_hash = Column(String(64), nullable=False)
    resume_text_summary = Column(Text, nullable=False)
    parsed_skills_json = Column(Text, nullable=False)
    education_level = Column(String(50), nullable=False)
    years_experience = Column(Float, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    candidate = relationship("Candidate", back_populates="resume_artifacts")


# Core 6: Skill
class Skill(Base):
    __tablename__ = "skills"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
    }

    skill_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    category = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    candidate_skills = relationship("CandidateSkill", back_populates="skill")
    requisition_skills = relationship(
        "RequisitionRequiredSkill",
        back_populates="skill",
    )


# Core 7: CandidateSkill
class CandidateSkill(Base):
    __tablename__ = "candidate_skills"
    __table_args__ = (
        UniqueConstraint("candidate_id", "skill_id", name="uq_cand_skill"),
        CheckConstraint(
            "proficiency_level >= 1 AND proficiency_level <= 5",
            name="check_proficiency_range",
        ),
        {
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
        },
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(
        String(50),
        ForeignKey("candidates.candidate_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    skill_id = Column(
        Integer,
        ForeignKey("skills.skill_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    proficiency_level = Column(Integer, default=3, nullable=False)
    years_experience = Column(Float, default=1.0, nullable=False)

    candidate = relationship("Candidate", back_populates="candidate_skills")
    skill = relationship("Skill", back_populates="candidate_skills")


# Supporting: RequisitionRequiredSkill
class RequisitionRequiredSkill(Base):
    __tablename__ = "requisition_required_skills"
    __table_args__ = (
        UniqueConstraint("requisition_id", "skill_id", name="uq_req_skill"),
        {
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
        },
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    requisition_id = Column(
        String(50),
        ForeignKey("job_requisitions.requisition_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    skill_id = Column(
        Integer,
        ForeignKey("skills.skill_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    is_required = Column(Boolean, default=True, nullable=False)
    min_experience_years = Column(Float, default=1.0, nullable=False)

    requisition = relationship(
        "JobRequisition",
        back_populates="required_skills",
    )
    skill = relationship("Skill", back_populates="requisition_skills")


# Core 8: ScreeningRule
class ScreeningRule(Base):
    __tablename__ = "screening_rules"
    __table_args__ = (
        CheckConstraint(
            "skill_weight >= 0 AND experience_weight >= 0 "
            "AND assessment_weight >= 0",
            name="check_weights_non_neg",
        ),
        CheckConstraint(
            "passing_threshold >= 0 AND passing_threshold <= 100",
            name="check_threshold_range",
        ),
        {
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
        },
    )

    rule_id = Column(Integer, primary_key=True, autoincrement=True)
    requisition_id = Column(
        String(50),
        ForeignKey("job_requisitions.requisition_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rule_version = Column(String(20), default="1.0", nullable=False)
    skill_weight = Column(Float, default=0.60, nullable=False)
    experience_weight = Column(Float, default=0.25, nullable=False)
    assessment_weight = Column(Float, default=0.15, nullable=False)
    passing_threshold = Column(Float, default=70.0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    requisition = relationship(
        "JobRequisition",
        back_populates="screening_rules",
    )


# Supporting: CandidateScreeningResult
class CandidateScreeningResult(Base):
    __tablename__ = "candidate_screening_results"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    application_id = Column(
        String(120),
        ForeignKey("applications.application_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rule_version = Column(String(20), nullable=False)
    skill_match_score = Column(Float, nullable=False)
    experience_score = Column(Float, nullable=False)
    assessment_score = Column(Float, nullable=False)
    final_score = Column(Float, nullable=False)
    threshold = Column(Float, nullable=False)
    decision = Column(String(20), nullable=False)
    reason_codes_json = Column(Text, nullable=False)
    evaluated_at = Column(DateTime, default=utc_now, nullable=False)

    application = relationship(
        "Application",
        back_populates="screening_results",
    )


# Core 9: Interviewer
class Interviewer(Base):
    __tablename__ = "interviewers"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
    }

    interviewer_id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    department_id = Column(
        Integer,
        ForeignKey("departments.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    title = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    department = relationship("Department", back_populates="interviewers")
    assignments = relationship(
        "InterviewerAssignment",
        back_populates="interviewer",
    )
    feedback_records = relationship(
        "Feedback",
        back_populates="interviewer",
    )


# Core 10: Interview
class Interview(Base):
    __tablename__ = "interviews"
    __table_args__ = (
        CheckConstraint(
            "scheduled_end > scheduled_start",
            name="check_interview_time_order",
        ),
        {
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
        },
    )

    interview_id = Column(String(50), primary_key=True)
    application_id = Column(
        String(120),
        ForeignKey("applications.application_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    round_number = Column(Integer, default=1, nullable=False)
    round_type = Column(SQLEnum(RoundType), nullable=False)
    scheduled_start = Column(DateTime, nullable=False, index=True)
    scheduled_end = Column(DateTime, nullable=False, index=True)
    status = Column(
        SQLEnum(InterviewStatus),
        default=InterviewStatus.SCHEDULED,
        nullable=False,
        index=True,
    )
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    application = relationship("Application", back_populates="interviews")
    assignments = relationship(
        "InterviewerAssignment",
        back_populates="interview",
    )
    feedback_records = relationship(
        "Feedback",
        back_populates="interview",
    )


# Supporting: InterviewerAssignment
class InterviewerAssignment(Base):
    __tablename__ = "interviewer_assignments"
    __table_args__ = (
        UniqueConstraint(
            "interview_id",
            "interviewer_id",
            name="uq_interview_interviewer",
        ),
        {
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
        },
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    interview_id = Column(
        String(50),
        ForeignKey("interviews.interview_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    interviewer_id = Column(
        String(50),
        ForeignKey("interviewers.interviewer_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    assigned_at = Column(DateTime, default=utc_now, nullable=False)

    interview = relationship("Interview", back_populates="assignments")
    interviewer = relationship("Interviewer", back_populates="assignments")


# Core 11: Feedback
class Feedback(Base):
    __tablename__ = "feedback"
    __table_args__ = (
        UniqueConstraint(
            "interview_id",
            "interviewer_id",
            name="uq_feedback_per_interviewer",
        ),
        CheckConstraint(
            "technical_rating >= 1 AND technical_rating <= 5",
            name="check_fb_tech_rating",
        ),
        CheckConstraint(
            "communication_rating >= 1 AND communication_rating <= 5",
            name="check_fb_comm_rating",
        ),
        CheckConstraint(
            "problem_solving_rating >= 1 AND problem_solving_rating <= 5",
            name="check_fb_prob_rating",
        ),
        CheckConstraint(
            "overall_score >= 1.0 AND overall_score <= 5.0",
            name="check_fb_overall_score",
        ),
        {
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
        },
    )

    feedback_id = Column(String(120), primary_key=True)
    interview_id = Column(
        String(50),
        ForeignKey("interviews.interview_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    interviewer_id = Column(
        String(50),
        ForeignKey("interviewers.interviewer_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    technical_rating = Column(Integer, nullable=False)
    communication_rating = Column(Integer, nullable=False)
    problem_solving_rating = Column(Integer, nullable=False)
    overall_score = Column(Float, nullable=False)
    recommendation = Column(SQLEnum(RecommendationEnum), nullable=False)
    notes = Column(Text, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    submitted_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    interview = relationship("Interview", back_populates="feedback_records")
    interviewer = relationship("Interviewer", back_populates="feedback_records")


# Core 12: Offer
class Offer(Base):
    __tablename__ = "offers"
    __table_args__ = (
        CheckConstraint("base_salary > 0", name="check_base_salary_positive"),
        {
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
        },
    )

    offer_id = Column(String(50), primary_key=True)
    application_id = Column(
        String(120),
        ForeignKey("applications.application_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    base_salary = Column(Float, nullable=False)
    sign_on_bonus = Column(Float, default=0.0, nullable=False)
    equity_shares = Column(Integer, default=0, nullable=False)
    currency = Column(String(10), default="USD", nullable=False)
    status = Column(
        SQLEnum(OfferStatus),
        default=OfferStatus.DRAFT,
        nullable=False,
        index=True,
    )
    is_out_of_band = Column(Boolean, default=False, nullable=False)
    exception_approved_by = Column(String(100), nullable=True)
    issued_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    responded_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    application = relationship("Application", back_populates="offers")
    approvals = relationship("OfferApproval", back_populates="offer")


# Supporting: RequisitionApproval
class RequisitionApproval(Base):
    __tablename__ = "requisition_approvals"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
    }

    approval_id = Column(Integer, primary_key=True, autoincrement=True)
    requisition_id = Column(
        String(50),
        ForeignKey("job_requisitions.requisition_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    approver_id = Column(String(50), nullable=False)
    status = Column(
        SQLEnum(ApprovalStatus),
        default=ApprovalStatus.PENDING,
        nullable=False,
    )
    comments = Column(String(255), nullable=True)
    decided_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    requisition = relationship(
        "JobRequisition",
        back_populates="approvals",
    )


# Supporting: OfferApproval
class OfferApproval(Base):
    __tablename__ = "offer_approvals"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
    }

    approval_id = Column(Integer, primary_key=True, autoincrement=True)
    offer_id = Column(
        String(50),
        ForeignKey("offers.offer_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    approver_id = Column(String(50), nullable=False)
    status = Column(
        SQLEnum(ApprovalStatus),
        default=ApprovalStatus.PENDING,
        nullable=False,
    )
    comments = Column(String(255), nullable=True)
    decided_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    offer = relationship("Offer", back_populates="approvals")


# Supporting: ApplicationEvent
class ApplicationEvent(Base):
    __tablename__ = "application_events"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
    }

    event_id = Column(Integer, primary_key=True, autoincrement=True)
    application_id = Column(
        String(120),
        ForeignKey("applications.application_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    from_stage = Column(String(50), nullable=False)
    to_stage = Column(String(50), nullable=False)
    actor = Column(String(100), nullable=False)
    reason = Column(String(255), nullable=False)
    rule_version = Column(String(20), default="1.0", nullable=False)
    event_timestamp = Column(
        DateTime,
        default=utc_now,
        nullable=False,
        index=True,
    )

    application = relationship("Application", back_populates="events")


# Supporting: AuditEvent
class AuditEvent(Base):
    __tablename__ = "audit_events"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
    }

    audit_id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(String(120), nullable=False, index=True)
    action = Column(String(50), nullable=False)
    previous_state_json = Column(Text, nullable=True)
    new_state_json = Column(Text, nullable=True)
    actor = Column(String(100), nullable=False)
    timestamp = Column(DateTime, default=utc_now, nullable=False, index=True)
    reason = Column(String(255), nullable=True)


# Supporting: DuplicateApplicationAttempt
class DuplicateApplicationAttempt(Base):
    __tablename__ = "duplicate_application_attempts"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
    }

    attempt_id = Column(String(120), primary_key=True)
    candidate_id = Column(
        String(50),
        ForeignKey("candidates.candidate_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    requisition_id = Column(
        String(50),
        ForeignKey("job_requisitions.requisition_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status = Column(String(50), default="BLOCKED_DUPLICATE", nullable=False)
    attempted_at = Column(DateTime, default=utc_now, nullable=False)
    reason = Column(String(255), nullable=False)


# Supporting: AnomalyRecord
class AnomalyRecord(Base):
    __tablename__ = "anomaly_records"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
    }

    issue_id = Column(String(50), primary_key=True)
    issue_type = Column(String(50), nullable=False, index=True)
    affected_entity_type = Column(String(50), nullable=False)
    affected_record_id = Column(String(120), nullable=False)
    expected_decision = Column(String(100), nullable=False)
    severity = Column(SQLEnum(AnomalySeverity), nullable=False)
    detection_result = Column(
        SQLEnum(AnomalyDetectionResult),
        nullable=False,
    )
    explanation = Column(Text, nullable=False)
    recommended_action = Column(Text, nullable=False)
    detected_at = Column(
        DateTime,
        default=utc_now,
        nullable=False,
        index=True,
    )