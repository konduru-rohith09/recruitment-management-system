import pytest
from src.validation import DataValidator
from src.metrics import MetricsCalculator
from src.audit import AuditService
from src.generate_data import SyntheticDataGenerator


def test_data_validator_comprehensive_suite(test_db, tmp_path):
    """Verify DataValidator executes and passes all integrity checks on clean synthetic seed."""
    gen = SyntheticDataGenerator(seed=20261022, scale="starter", output_dir=str(tmp_path))
    gen.generate_and_seed(test_db)

    report_path = str(tmp_path / "val_report.json")
    summary = DataValidator.run_all_validations(test_db, export_report_path=report_path)

    assert summary["total_checks"] >= 12
    assert summary["failed_checks"] == 0
    assert summary["passed_checks"] == summary["total_checks"]


def test_metrics_empty_denominator_safety(test_db):
    """Verify metric calculations never raise ZeroDivisionError when database is empty."""
    metrics = MetricsCalculator.compute_all_metrics(test_db)

    assert metrics["screening"]["screening_pass_rate_pct"] == 0.0
    assert metrics["screening"]["average_screening_score"] == 0.0
    assert metrics["interviews"]["interview_completion_rate_pct"] == 0.0
    assert metrics["offers"]["offer_acceptance_rate_pct"] == 0.0
    assert metrics["funnel_rates"]["withdrawal_rate_pct"] == 0.0
    assert metrics["funnel_rates"]["rejection_rate_pct"] == 0.0
    assert metrics["funnel_rates"]["avg_time_to_decision_days"] == 0.0


def test_all_five_anomalies_detected(test_db, tmp_path):
    """Verify AuditService detects all 5 required anomaly scenarios."""
    gen = SyntheticDataGenerator(seed=20261022, scale="starter", output_dir=str(tmp_path))
    gen.generate_and_seed(test_db)

    anomalies = AuditService.scan_for_anomalies(test_db)
    detected_types = {a.issue_type for a in anomalies}

    expected_types = {
        "INTERVIEWER_UNAVAILABLE",
        "DUPLICATE_APPLICATION",
        "MISSING_FEEDBACK",
        "SALARY_OUTSIDE_BAND",
        "CLOSED_ROLE_ACTIVE_APPLICATIONS",
    }
    for et in expected_types:
        assert et in detected_types, f"Anomaly scenario {et} was not detected by audit scanner!"
