import pytest
from src.screening import ScreeningEngine, ScreeningError
from src.models import (
    Department,
    JobRequisition,
    Candidate,
    Application,
    Skill,
    CandidateSkill,
    RequisitionRequiredSkill,
    ScreeningRule,
    RequisitionStatus,
    ApplicationStage,
)


def test_rule_weight_validation():
    """Verify ScreeningEngine rejects weights that do not sum to 1.0 or are negative."""
    # Invalid sum (> 1.0)
    rule_bad_sum = ScreeningRule(skill_weight=0.6, experience_weight=0.3, assessment_weight=0.2, passing_threshold=70.0)
    with pytest.raises(ScreeningError, match="must sum to 1.0"):
        ScreeningEngine.validate_rule_weights(rule_bad_sum)

    # Negative weight
    rule_neg = ScreeningRule(skill_weight=-0.1, experience_weight=0.7, assessment_weight=0.4, passing_threshold=70.0)
    with pytest.raises(ScreeningError, match="cannot be negative"):
        ScreeningEngine.validate_rule_weights(rule_neg)

    # Valid rule
    rule_valid = ScreeningRule(skill_weight=0.60, experience_weight=0.25, assessment_weight=0.15, passing_threshold=70.0)
    ScreeningEngine.validate_rule_weights(rule_valid)


def test_screening_evaluation_and_threshold_boundaries(test_db):
    """Test screening evaluation score calculations and exact threshold boundaries."""
    dept = Department(code="ENG", name="Engineering", cost_center="CC-100")
    test_db.add(dept)
    test_db.flush()

    req = JobRequisition(
        requisition_id="REQ-2026-000100",
        title="Software Engineer",
        department_id=dept.id,
        hiring_manager_id="EMP-000001",
        status=RequisitionStatus.OPEN,
        min_experience_years=3.0,
        min_salary=100000.0,
        max_salary=140000.0,
    )
    s1 = Skill(name="Python", category="Backend")
    s2 = Skill(name="SQL", category="Database")
    test_db.add_all([req, s1, s2])
    test_db.flush()

    test_db.add(RequisitionRequiredSkill(requisition_id=req.requisition_id, skill_id=s1.skill_id, is_required=True, min_experience_years=2.0))
    test_db.add(RequisitionRequiredSkill(requisition_id=req.requisition_id, skill_id=s2.skill_id, is_required=True, min_experience_years=2.0))

    rule = ScreeningRule(
        requisition_id=req.requisition_id,
        rule_version="1.0",
        skill_weight=0.60,
        experience_weight=0.25,
        assessment_weight=0.15,
        passing_threshold=70.0,
        is_active=True,
    )
    test_db.add(rule)

    # High qualification candidate (Pass)
    cand_high = Candidate(
        candidate_id="CAND-000101",
        first_name="High",
        last_name="Scorer",
        email="high@test.com",
        phone="555-101",
        location="Remote",
        total_experience_years=5.0,
    )
    test_db.add(cand_high)
    test_db.flush()

    test_db.add(CandidateSkill(candidate_id=cand_high.candidate_id, skill_id=s1.skill_id, proficiency_level=5, years_experience=5.0))
    test_db.add(CandidateSkill(candidate_id=cand_high.candidate_id, skill_id=s2.skill_id, proficiency_level=5, years_experience=5.0))

    app_high = Application(
        application_id=f"APP-{req.requisition_id}-{cand_high.candidate_id}",
        candidate_id=cand_high.candidate_id,
        requisition_id=req.requisition_id,
        current_stage=ApplicationStage.APPLIED,
    )
    test_db.add(app_high)
    test_db.commit()

    res_high = ScreeningEngine.evaluate_application(test_db, app_high.application_id, assessment_score=85.0)
    assert res_high.decision == "PASS"
    assert res_high.final_score >= 70.0
    assert "SURPASSED_PASSING_THRESHOLD" in res_high.reason_codes_json

    # Low qualification candidate (Fail)
    cand_low = Candidate(
        candidate_id="CAND-000102",
        first_name="Low",
        last_name="Scorer",
        email="low@test.com",
        phone="555-102",
        location="Remote",
        total_experience_years=0.5,
    )
    test_db.add(cand_low)
    test_db.flush()
    # Missing required skills entirely
    app_low = Application(
        application_id=f"APP-{req.requisition_id}-{cand_low.candidate_id}",
        candidate_id=cand_low.candidate_id,
        requisition_id=req.requisition_id,
        current_stage=ApplicationStage.APPLIED,
    )
    test_db.add(app_low)
    test_db.commit()

    res_low = ScreeningEngine.evaluate_application(test_db, app_low.application_id, assessment_score=40.0)
    assert res_low.decision == "FAIL"
    assert res_low.final_score < 70.0
    assert "FAILED_PASSING_THRESHOLD" in res_low.reason_codes_json
