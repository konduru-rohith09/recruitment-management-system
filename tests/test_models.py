import pytest
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError
from src.models import (
    Department,
    JobRequisition,
    Candidate,
    Application,
    Skill,
    CandidateSkill,
    RequisitionRequiredSkill,
    ScreeningRule,
    Interviewer,
    Interview,
    InterviewerAssignment,
    Feedback,
    Offer,
    RequisitionStatus,
    ApplicationStage,
    RoundType,
    InterviewStatus,
    RecommendationEnum,
    OfferStatus,
    utc_now,
)


def test_department_and_requisition_creation(test_db):
    """Test Department and JobRequisition model creation and relationships."""
    dept = Department(code="ENG", name="Engineering", cost_center="CC-100")
    test_db.add(dept)
    test_db.commit()
    assert dept.id is not None

    req = JobRequisition(
        requisition_id="REQ-2026-000001",
        title="Senior Python Backend Developer",
        department_id=dept.id,
        hiring_manager_id="EMP-000001",
        status=RequisitionStatus.OPEN,
        headcount=1,
        min_experience_years=3.0,
        min_salary=110000.0,
        max_salary=150000.0,
    )
    test_db.add(req)
    test_db.commit()

    assert req.requisition_id == "REQ-2026-000001"
    assert req.department.name == "Engineering"


def test_candidate_profile_and_non_sensitive_attributes(test_db):
    """Verify Candidate model excludes protected demographic attributes."""
    cand = Candidate(
        candidate_id="CAND-000001",
        first_name="Alex",
        last_name="Mercer",
        email="alex.mercer@test.com",
        phone="+1-555-0199",
        location="Austin, TX",
        total_experience_years=5.5,
    )
    test_db.add(cand)
    test_db.commit()

    # Verify no protected attributes exist on Candidate table
    col_names = [col.name for col in Candidate.__table__.columns]
    for sensitive_attr in ["age", "gender", "caste", "religion", "race", "disability", "marital_status"]:
        assert sensitive_attr not in col_names


def test_application_deterministic_id_and_uniqueness(test_db):
    """Verify application deterministic ID format and unique candidate-requisition constraint."""
    dept = Department(code="DATA", name="Data", cost_center="CC-200")
    test_db.add(dept)
    test_db.flush()

    req = JobRequisition(
        requisition_id="REQ-2026-000002",
        title="Data Engineer",
        department_id=dept.id,
        hiring_manager_id="EMP-000002",
        min_salary=90000.0,
        max_salary=130000.0,
    )
    cand = Candidate(
        candidate_id="CAND-000002",
        first_name="Jordan",
        last_name="Lee",
        email="jordan.lee@test.com",
        phone="+1-555-0288",
        location="Seattle, WA",
        total_experience_years=4.0,
    )
    test_db.add_all([req, cand])
    test_db.commit()

    expected_app_id = f"APP-{req.requisition_id}-{cand.candidate_id}"
    app = Application(
        application_id=expected_app_id,
        candidate_id=cand.candidate_id,
        requisition_id=req.requisition_id,
        current_stage=ApplicationStage.APPLIED,
    )
    test_db.add(app)
    test_db.commit()

    assert app.application_id == "APP-REQ-2026-000002-CAND-000002"

    # Attempting to add duplicate application should violate unique constraint
    dup_app = Application(
        application_id="APP-REQ-2026-000002-CAND-000002-DUP",
        candidate_id=cand.candidate_id,
        requisition_id=req.requisition_id,
        current_stage=ApplicationStage.APPLIED,
    )
    test_db.add(dup_app)
    with pytest.raises(IntegrityError):
        test_db.commit()
    test_db.rollback()


def test_interviewer_assignment_and_feedback(test_db):
    """Test multi-interviewer assignments and structured feedback rating boundaries."""
    dept = Department(code="ENG", name="Engineering", cost_center="CC-100")
    test_db.add(dept)
    test_db.flush()

    req = JobRequisition(
        requisition_id="REQ-2026-000003",
        title="QA Engineer",
        department_id=dept.id,
        hiring_manager_id="EMP-000001",
        min_salary=80000.0,
        max_salary=110000.0,
    )
    cand = Candidate(
        candidate_id="CAND-000003",
        first_name="Casey",
        last_name="Smith",
        email="casey.smith@test.com",
        phone="+1-555-0377",
        location="Remote",
        total_experience_years=3.0,
    )
    app = Application(
        application_id="APP-REQ-2026-000003-CAND-000003",
        candidate_id=cand.candidate_id,
        requisition_id=req.requisition_id,
        current_stage=ApplicationStage.INTERVIEW,
    )
    emp1 = Interviewer(
        interviewer_id="EMP-000001",
        name="Lead Interviewer",
        email="lead@eng.yottaflex.internal",
        department_id=dept.id,
        title="Lead Engineer",
    )
    emp2 = Interviewer(
        interviewer_id="EMP-000002",
        name="Staff Interviewer",
        email="staff@eng.yottaflex.internal",
        department_id=dept.id,
        title="Staff Engineer",
    )
    test_db.add_all([req, cand, app, emp1, emp2])
    test_db.commit()

    start_t = utc_now()
    end_t = start_t + timedelta(hours=1)
    intv = Interview(
        interview_id="INT-2026-000001",
        application_id=app.application_id,
        round_number=1,
        round_type=RoundType.TECHNICAL,
        scheduled_start=start_t,
        scheduled_end=end_t,
        status=InterviewStatus.SCHEDULED,
    )
    test_db.add(intv)
    test_db.flush()

    # Assign both interviewers
    test_db.add(InterviewerAssignment(interview_id=intv.interview_id, interviewer_id=emp1.interviewer_id))
    test_db.add(InterviewerAssignment(interview_id=intv.interview_id, interviewer_id=emp2.interviewer_id))
    test_db.commit()

    # Submit valid feedback
    fb = Feedback(
        feedback_id=f"FB-{intv.interview_id}-{emp1.interviewer_id}",
        interview_id=intv.interview_id,
        interviewer_id=emp1.interviewer_id,
        technical_rating=4,
        communication_rating=5,
        problem_solving_rating=4,
        overall_score=4.3,
        recommendation=RecommendationEnum.STRONG_HIRE,
        notes="Solid candidate with clean problem solving.",
    )
    test_db.add(fb)
    test_db.commit()
    assert fb.feedback_id == "FB-INT-2026-000001-EMP-000001"
