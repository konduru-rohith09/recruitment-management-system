import pytest
from datetime import datetime, timedelta
from src.scheduling import SchedulingService, InterviewerConflictError, SchedulingError
from src.models import (
    Department,
    JobRequisition,
    Candidate,
    Application,
    Interviewer,
    Interview,
    RoundType,
    InterviewStatus,
    utc_now,
)


def test_interviewer_availability_and_conflict_detection(test_db):
    """Test overlapping interview bookings are detected and blocked."""
    dept = Department(code="SEC", name="Security", cost_center="CC-500")
    test_db.add(dept)
    test_db.flush()

    req = JobRequisition(
        requisition_id="REQ-2026-000200",
        title="Security Analyst",
        department_id=dept.id,
        hiring_manager_id="EMP-000001",
        min_salary=95000.0,
        max_salary=135000.0,
    )
    cand1 = Candidate(candidate_id="CAND-000201", first_name="A", last_name="B", email="a@b.com", phone="1", location="L")
    cand2 = Candidate(candidate_id="CAND-000202", first_name="C", last_name="D", email="c@d.com", phone="2", location="L")
    app1 = Application(application_id="APP-REQ-2026-000200-CAND-000201", candidate_id=cand1.candidate_id, requisition_id=req.requisition_id)
    app2 = Application(application_id="APP-REQ-2026-000200-CAND-000202", candidate_id=cand2.candidate_id, requisition_id=req.requisition_id)
    emp = Interviewer(interviewer_id="EMP-000201", name="Expert Interviewer", email="exp@sec.internal", department_id=dept.id, title="Lead", is_active=True)

    test_db.add_all([req, cand1, cand2, app1, app2, emp])
    test_db.commit()

    # Schedule first interview 10:00 to 11:00
    base_t = datetime(2026, 3, 1, 10, 0, 0)
    int1 = SchedulingService.schedule_interview(
        db=test_db,
        interview_id="INT-2026-000201",
        application_id=app1.application_id,
        round_number=1,
        round_type=RoundType.TECHNICAL,
        scheduled_start=base_t,
        scheduled_end=base_t + timedelta(hours=1),
        interviewer_ids=[emp.interviewer_id],
    )
    assert int1.interview_id == "INT-2026-000201"

    # Attempt overlapping booking for same interviewer 10:30 to 11:30 -> Must raise InterviewerConflictError
    with pytest.raises(InterviewerConflictError, match="Conflict detected"):
        SchedulingService.schedule_interview(
            db=test_db,
            interview_id="INT-2026-000202",
            application_id=app2.application_id,
            round_number=1,
            round_type=RoundType.TECHNICAL,
            scheduled_start=base_t + timedelta(minutes=30),
            scheduled_end=base_t + timedelta(minutes=90),
            interviewer_ids=[emp.interviewer_id],
        )


def test_inactive_interviewer_blocked(test_db):
    """Test assigning an inactive interviewer is blocked."""
    dept = Department(code="OPS", name="Operations", cost_center="CC-600")
    test_db.add(dept)
    test_db.flush()

    req = JobRequisition(
        requisition_id="REQ-2026-000203",
        title="DevOps",
        department_id=dept.id,
        hiring_manager_id="EMP-000001",
        min_salary=90000.0,
        max_salary=120000.0,
    )
    cand = Candidate(candidate_id="CAND-000203", first_name="E", last_name="F", email="e@f.com", phone="3", location="L")
    app = Application(application_id="APP-REQ-2026-000203-CAND-000203", candidate_id=cand.candidate_id, requisition_id=req.requisition_id)
    inactive_emp = Interviewer(interviewer_id="EMP-000202", name="Inactive Staff", email="inact@ops.internal", department_id=dept.id, title="Eng", is_active=False)

    test_db.add_all([req, cand, app, inactive_emp])
    test_db.commit()

    base_t = datetime(2026, 3, 2, 14, 0, 0)
    with pytest.raises(InterviewerConflictError, match="currently inactive"):
        SchedulingService.schedule_interview(
            db=test_db,
            interview_id="INT-2026-000203",
            application_id=app.application_id,
            round_number=1,
            round_type=RoundType.BEHAVIORAL,
            scheduled_start=base_t,
            scheduled_end=base_t + timedelta(hours=1),
            interviewer_ids=[inactive_emp.interviewer_id],
        )


def test_invalid_interview_time_ordering(test_db):
    """Test interview end time must be strictly after start time."""
    dept = Department(code="OPS", name="Operations", cost_center="CC-600")
    test_db.add(dept)
    test_db.flush()

    req = JobRequisition(
        requisition_id="REQ-2026-000204",
        title="SRE",
        department_id=dept.id,
        hiring_manager_id="EMP-000001",
        min_salary=90000.0,
        max_salary=120000.0,
    )
    cand = Candidate(candidate_id="CAND-000204", first_name="G", last_name="H", email="g@h.com", phone="4", location="L")
    app = Application(application_id="APP-REQ-2026-000204-CAND-000204", candidate_id=cand.candidate_id, requisition_id=req.requisition_id)
    emp = Interviewer(interviewer_id="EMP-000203", name="SRE Lead", email="sre@ops.internal", department_id=dept.id, title="Lead", is_active=True)

    test_db.add_all([req, cand, app, emp])
    test_db.commit()

    base_t = datetime(2026, 3, 3, 10, 0, 0)
    with pytest.raises(SchedulingError, match="strictly after start time"):
        SchedulingService.schedule_interview(
            db=test_db,
            interview_id="INT-2026-000204",
            application_id=app.application_id,
            round_number=1,
            round_type=RoundType.HR,
            scheduled_start=base_t,
            scheduled_end=base_t - timedelta(minutes=15),
            interviewer_ids=[emp.interviewer_id],
        )
