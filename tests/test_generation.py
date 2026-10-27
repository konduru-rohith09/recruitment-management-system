import os
import pytest
from src.generate_data import SyntheticDataGenerator


def test_starter_generation_target_counts(test_db, tmp_path):
    """Test starter scale generation produces expected baseline entities and relationships."""
    gen = SyntheticDataGenerator(seed=20261022, scale="starter", output_dir=str(tmp_path))
    summary = gen.generate_and_seed(test_db)

    assert summary["requisitions"] == 10
    assert summary["candidates"] == 100
    assert summary["applications"] == 150
    assert summary["interviews"] >= 20
    assert summary["offers"] >= 5
    assert summary["anomalies"] >= 4

    # Verify CSV and JSON files were written to output_dir
    assert os.path.exists(tmp_path / "job_requisitions.csv")
    assert os.path.exists(tmp_path / "candidates.csv")
    assert os.path.exists(tmp_path / "applications.csv")
    assert os.path.exists(tmp_path / "interviews.csv")
    assert os.path.exists(tmp_path / "offers.csv")


def test_ground_truth_separation(test_db, tmp_path):
    """Verify ground truth anomaly file exists and contains all 5 required scenario types."""
    gen = SyntheticDataGenerator(seed=20261022, scale="starter", output_dir=str(tmp_path))
    gen.generate_and_seed(test_db)

    gt_file = "data/ground_truth/ground_truth.json"
    assert os.path.exists(gt_file)

    import json
    with open(gt_file, "r", encoding="utf-8") as f:
        gt_data = json.load(f)

    issue_types = {item["issue_type"] for item in gt_data}
    required_types = {
        "INTERVIEWER_UNAVAILABLE",
        "DUPLICATE_APPLICATION",
        "MISSING_FEEDBACK",
        "SALARY_OUTSIDE_BAND",
        "CLOSED_ROLE_ACTIVE_APPLICATIONS",
    }
    for req_type in required_types:
        assert req_type in issue_types
