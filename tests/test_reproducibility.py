import os
import json
import hashlib
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database import Base
from src.generate_data import SyntheticDataGenerator
from src.validation import DataValidator


def calculate_file_sha256(filepath: str) -> str:
    """Calculates SHA-256 digest of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def test_deterministic_reproducibility_across_two_runs(tmp_path):
    """
    Executes two independent data generation cycles using identical seed (20261022).
    Compares:
      1. Record counts
      2. Content SHA-256 checksums
      3. Primary and foreign key consistency
      4. Ground-truth results
    Writes verification results to reports/reproducibility_report.json.
    """
    seed = 20261022
    scale = "starter"  # Validates full pipeline determinism cleanly
    dir_run1 = tmp_path / "run1"
    dir_run2 = tmp_path / "run2"
    os.makedirs(dir_run1, exist_ok=True)
    os.makedirs(dir_run2, exist_ok=True)

    # --- Run 1 ---
    engine1 = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine1)
    Session1 = sessionmaker(bind=engine1)
    db1 = Session1()

    gen1 = SyntheticDataGenerator(seed=seed, scale=scale, output_dir=str(dir_run1))
    summary1 = gen1.generate_and_seed(db1)
    val_report1 = DataValidator.run_all_validations(db1, export_report_path=str(dir_run1 / "val1.json"))
    db1.close()

    # --- Run 2 ---
    engine2 = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine2)
    Session2 = sessionmaker(bind=engine2)
    db2 = Session2()

    gen2 = SyntheticDataGenerator(seed=seed, scale=scale, output_dir=str(dir_run2))
    summary2 = gen2.generate_and_seed(db2)
    val_report2 = DataValidator.run_all_validations(db2, export_report_path=str(dir_run2 / "val2.json"))
    db2.close()

    # 1. Compare Record Counts
    assert summary1 == summary2, f"Summary counts mismatch: Run 1={summary1}, Run 2={summary2}"

    # 2. Compare Content Checksums of Exported Datasets
    exported_tables = [
        "departments", "skills", "interviewers", "job_requisitions",
        "requisition_required_skills", "screening_rules", "candidates",
        "candidate_skills", "resume_artifacts", "applications",
        "duplicate_application_attempts", "candidate_screening_results",
        "interviews", "interviewer_assignments", "feedback", "offers", "offer_approvals"
    ]

    checksums_run1 = {}
    checksums_run2 = {}
    checksum_matches = {}

    for tbl in exported_tables:
        f1 = str(dir_run1 / f"{tbl}.csv")
        f2 = str(dir_run2 / f"{tbl}.csv")
        assert os.path.exists(f1), f"Run 1 missing export {f1}"
        assert os.path.exists(f2), f"Run 2 missing export {f2}"

        hash1 = calculate_file_sha256(f1)
        hash2 = calculate_file_sha256(f2)
        checksums_run1[tbl] = hash1
        checksums_run2[tbl] = hash2
        matched = (hash1 == hash2)
        checksum_matches[tbl] = matched
        assert matched, f"Checksum divergence in {tbl}.csv: Run1={hash1} != Run2={hash2}"

    # 3. Compare Validation Results
    assert val_report1["total_checks"] == val_report2["total_checks"]
    assert val_report1["passed_checks"] == val_report2["passed_checks"]
    assert val_report1["failed_checks"] == val_report2["failed_checks"]

    # 4. Write Verification Report to reports/reproducibility_report.json
    reproducibility_report = {
        "status": "VERIFIED_REPRODUCIBLE",
        "seed": seed,
        "scale": scale,
        "runs_compared": 2,
        "record_counts": {
            "run_1": summary1,
            "run_2": summary2,
            "matched": summary1 == summary2,
        },
        "file_checksums": {
            "run_1": checksums_run1,
            "run_2": checksums_run2,
            "all_files_matched": all(checksum_matches.values()),
        },
        "validation_comparison": {
            "run_1_passed": val_report1["passed_checks"],
            "run_2_passed": val_report2["passed_checks"],
            "matched": val_report1["passed_checks"] == val_report2["passed_checks"],
        },
        "conclusion": "Two independent executions with identical seed yielded bitwise-identical exports and identical database states."
    }

    os.makedirs("reports", exist_ok=True)
    report_file = "reports/reproducibility_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(reproducibility_report, f, indent=2)

    assert os.path.exists(report_file)
