import pytest
from datetime import datetime, timedelta
from src.workflow import WorkflowEngine, WorkflowError
from src.models import (
    Department,
    JobRequisition,
    Candidate,
    Application,
    Interviewer,
    Interview,
    InterviewerAssignment,
    Feedback,
    ApplicationEvent,
    ApplicationStage,
    RequisitionStatus,
    RoundType,
    InterviewStatus,
    RecommendationEnum,
    utc_now,
)


def test_missing_feedback_blocks_decision_pending(test_db):
    """Verify application cannot advance to DECISION_PENDING when assigned interviewer feedback is missing."""
    dept = Department(code="PROD", name="Product", cost_center="CC-300")
    test_db.add(dept)
    test_db.flush()

    req = JobRequisition(
        requisition_id="REQ-2026-000300",
        title="Product Manager",
        department_id=dept.id,
        hiring_manager_id="EMP-000001",
        status=RequisitionStatus.OPEN,
        min_salary=120000.0,
        max_salary=160000.0,
    )
    cand = Candidate(candidate_id="CAND-000301", first_name="Riley", last_name="Quinn", email="riley@pm.com", phone="1", location="L")
    app = Application(
        application_id="APP-REQ-2026-000300-CAND-000301",
        candidate_id=cand.candidate_id,
        requisition_id=req.requisition_id,
        current_stage=ApplicationStage.INTERVIEW,
    )
    emp = Interviewer(interviewer_id="EMP-000301", name="Product Director", email="pd@prod.internal", department_id=dept.id, title="Director", is_active=True)
    test_db.add_all([req, cand, app, emp])
    test_db.commit()

    intv = Interview(
        interview_id="INT-2026-000301",
        application_id=app.application_id,
        round_number=1,
        round_type=RoundType.BEHAVIORAL,
        scheduled_start=utc_now() - timedelta(hours=2),
        scheduled_end=utc_now() - timedelta(hours=1),
        status=InterviewStatus.COMPLETED,
    )
    test_db.add(intv)
    test_db.flush()
    test_db.add(InterviewerAssignment(interview_id=intv.interview_id, interviewer_id=emp.interviewer_id))
    test_db.commit()

    # Attempt transition without feedback -> Must raise WorkflowError
    with pytest.raises(WorkflowError, match="Missing required feedback"):
        WorkflowEngine.transition_stage(
            db=test_db,
            application_id=app.application_id,
            target_stage=ApplicationStage.DECISION_PENDING,
        )

    # Now submit required feedback
    WorkflowEngine.submit_feedback(
        db=test_db,
        interview_id=intv.interview_id,
        interviewer_id=emp.interviewer_id,
        technical_rating=4,
        communication_rating=5,
        problem_solving_rating=4,
        recommendation=RecommendationEnum.HIRE,
        notes="Strong domain insight and leadership.",
    )

    # Transition now succeeds
    updated_app = WorkflowEngine.transition_stage(
        db=test_db,
        application_id=app.application_id,
        target_stage=ApplicationStage.DECISION_PENDING,
    )
    assert updated_app.current_stage == ApplicationStage.DECISION_PENDING

    # Verify event logged
    events = test_db.query(ApplicationEvent).filter(ApplicationEvent.application_id == app.application_id).all()
    assert len(events) >= 1
    assert events[-1].to_stage == ApplicationStage.DECISION_PENDING.value


def test_invalid_lifecycle_transition_blocked(test_db):
    """Test skipping stages illegally (e.g. APPLIED -> ACCEPTED) is blocked."""
    dept = Department(code="PROD", name="Product", cost_center="CC-300")
    test_db.add(dept)
    test_db.flush()

    req = JobRequisition(
        requisition_id="REQ-2026-000302",
        title="Associate PM",
        department_id=dept.id,
        hiring_manager_id="EMP-000001",
        status=RequisitionStatus.OPEN,
        min_salary=80000.0,
        max_salary=110000.0,
    )
    cand = Candidate(candidate_id="CAND-000302", first_name="Morgan", last_name="Taylor", email="morgan@pm.com", phone="2", location="L")
    app = Application(
        application_id="APP-REQ-2026-000302-CAND-000302",
        candidate_id=cand.candidate_id,
        requisition_id=req.requisition_id,
        current_stage=ApplicationStage.APPLIED,
    )
    test_db.add_all([req, cand, app])
    test_db.commit()

    with pytest.raises(WorkflowError, match="Invalid stage transition"):
        WorkflowEngine.transition_stage(
            db=test_db,
            application_id=app.application_id,
            target_stage=ApplicationStage.ACCEPTED,
        )
