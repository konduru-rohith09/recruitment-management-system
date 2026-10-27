import json
import logging
import math
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.models import (
    JobRequisition,
    Candidate,
    Application,
    Interview,
    Offer,
    CandidateScreeningResult,
    ScreeningRule,
)
from src.audit import AuditService

logger = logging.getLogger("recruitment_system.validation")


class DataValidator:
    """Validate database integrity, constraints, and business rules."""

    @classmethod
    def run_all_validations(
        cls,
        db: Session,
        export_report_path: str = "reports/validation_summary.json",
    ) -> Dict[str, Any]:
        """Run integrity checks and optionally export a JSON report."""
        checks: List[Dict[str, Any]] = []

        def add_check(
            name: str,
            passed: bool,
            details: str,
            severity: str = "ERROR",
        ) -> None:
            checks.append(
                {
                    "check_name": name,
                    "status": "PASSED" if passed else "FAILED",
                    "severity": severity,
                    "details": details,
                }
            )

        # 1. Primary key uniqueness
        primary_key_checks = [
            (
                "PK_UNIQUENESS_REQUISITIONS",
                JobRequisition,
                JobRequisition.requisition_id,
                "Requisitions",
            ),
            (
                "PK_UNIQUENESS_CANDIDATES",
                Candidate,
                Candidate.candidate_id,
                "Candidates",
            ),
            (
                "PK_UNIQUENESS_APPLICATIONS",
                Application,
                Application.application_id,
                "Applications",
            ),
            (
                "PK_UNIQUENESS_INTERVIEWS",
                Interview,
                Interview.interview_id,
                "Interviews",
            ),
            (
                "PK_UNIQUENESS_OFFERS",
                Offer,
                Offer.offer_id,
                "Offers",
            ),
        ]

        for check_name, model, pk_column, label in primary_key_checks:
            total = db.query(pk_column).count()
            distinct_total = (
                db.query(func.count(func.distinct(pk_column))).scalar() or 0
            )

            add_check(
                check_name,
                total == distinct_total,
                f"{label} count: {total}, distinct primary keys: "
                f"{distinct_total}",
            )

        # 2. Foreign key integrity
        orphan_checks = [
            (
                "FK_INTEGRITY_APP_REQUISITION",
                Application,
                Application.requisition_id,
                JobRequisition,
                JobRequisition.requisition_id,
                "application-to-requisition",
            ),
            (
                "FK_INTEGRITY_APP_CANDIDATE",
                Application,
                Application.candidate_id,
                Candidate,
                Candidate.candidate_id,
                "application-to-candidate",
            ),
            (
                "FK_INTEGRITY_INTERVIEW_APP",
                Interview,
                Interview.application_id,
                Application,
                Application.application_id,
                "interview-to-application",
            ),
            (
                "FK_INTEGRITY_OFFER_APP",
                Offer,
                Offer.application_id,
                Application,
                Application.application_id,
                "offer-to-application",
            ),
        ]

        for (
            check_name,
            source_model,
            source_column,
            target_model,
            target_column,
            relationship_name,
        ) in orphan_checks:
            orphan_count = (
                db.query(source_model)
                .outerjoin(
                    target_model,
                    source_column == target_column,
                )
                .filter(target_column.is_(None))
                .count()
            )

            add_check(
                check_name,
                orphan_count == 0,
                f"Orphaned {relationship_name} references: {orphan_count}",
            )

        # 3. Interview and requisition date ordering
        invalid_interview_dates = (
            db.query(Interview)
            .filter(
                Interview.scheduled_end <= Interview.scheduled_start,
            )
            .count()
        )

        add_check(
            "DATE_ORDER_INTERVIEW_TIMES",
            invalid_interview_dates == 0,
            f"Interviews with end <= start: {invalid_interview_dates}",
        )

        invalid_req_dates = (
            db.query(JobRequisition)
            .filter(
                JobRequisition.closed_at.is_not(None),
                JobRequisition.opened_at.is_not(None),
                JobRequisition.closed_at < JobRequisition.opened_at,
            )
            .count()
        )

        add_check(
            "DATE_ORDER_REQUISITION_DATES",
            invalid_req_dates == 0,
            f"Requisitions with closed_at < opened_at: "
            f"{invalid_req_dates}",
        )

        # 4. Salary band validity
        invalid_salary_bands = (
            db.query(JobRequisition)
            .filter(
                (JobRequisition.min_salary < 0)
                | (JobRequisition.max_salary < JobRequisition.min_salary),
            )
            .count()
        )

        add_check(
            "SALARY_BAND_ORDERING",
            invalid_salary_bands == 0,
            f"Requisitions with invalid salary bands: "
            f"{invalid_salary_bands}",
        )

        # 5. Screening score consistency
        mismatched_screening_scores = 0
        missing_screening_values = 0
        screening_results = db.query(CandidateScreeningResult).all()

        for result in screening_results:
            components = (
                result.skill_match_score,
                result.experience_score,
                result.assessment_score,
                result.final_score,
                result.threshold,
            )

            if any(
                value is None
                or not math.isfinite(float(value))
                for value in components
            ):
                missing_screening_values += 1
                continue

            application = (
                db.query(Application)
                .filter(
                    Application.application_id == result.application_id,
                )
                .first()
            )

            if application is None:
                missing_screening_values += 1
                continue

            rule = (
                db.query(ScreeningRule)
                .filter(
                    ScreeningRule.requisition_id
                    == application.requisition_id,
                    ScreeningRule.rule_version == result.rule_version,
                )
                .first()
            )

            if rule is None:
                # Historical results cannot be verified without their rule.
                missing_screening_values += 1
                continue

            weights = (
                rule.skill_weight,
                rule.experience_weight,
                rule.assessment_weight,
            )

            if any(
                value is None or not math.isfinite(float(value))
                for value in weights
            ):
                missing_screening_values += 1
                continue

            expected = round(
                float(result.skill_match_score) * float(rule.skill_weight)
                + float(result.experience_score) * float(rule.experience_weight)
                + float(result.assessment_score) * float(rule.assessment_weight),
                2,
            )

            if abs(float(result.final_score) - expected) > 0.05:
                mismatched_screening_scores += 1

            for score_name, score in (
                ("skill_match_score", result.skill_match_score),
                ("experience_score", result.experience_score),
                ("assessment_score", result.assessment_score),
                ("final_score", result.final_score),
                ("threshold", result.threshold),
            ):
                if not 0 <= float(score) <= 100:
                    mismatched_screening_scores += 1
                    break

        add_check(
            "DERIVED_SCREENING_SCORES",
            mismatched_screening_scores == 0
            and missing_screening_values == 0,
            f"Screening results with invalid scores or arithmetic deviation: "
            f"{mismatched_screening_scores}; results that could not "
            f"be verified: {missing_screening_values}",
        )

        # 6. Run anomaly scanner
        anomalies = AuditService.scan_for_anomalies(db)

        anomaly_summary: Dict[str, Any] = {
            "total_detected": len(anomalies),
            "by_type": {},
            "by_severity": {},
        }

        for anomaly in anomalies:
            anomaly_summary["by_type"][anomaly.issue_type] = (
                anomaly_summary["by_type"].get(anomaly.issue_type, 0) + 1
            )

            severity = (
                anomaly.severity.value
                if hasattr(anomaly.severity, "value")
                else str(anomaly.severity)
            )

            anomaly_summary["by_severity"][severity] = (
                anomaly_summary["by_severity"].get(severity, 0) + 1
            )

        total_checks = len(checks)
        passed_checks = sum(
            1 for check in checks if check["status"] == "PASSED"
        )
        failed_checks = total_checks - passed_checks

        summary = {
            "timestamp": datetime.now().astimezone().isoformat(),
            "total_checks": total_checks,
            "passed_checks": passed_checks,
            "failed_checks": failed_checks,
            "warnings": sum(
                1
                for check in checks
                if check["severity"] == "WARNING"
                and check["status"] == "FAILED"
            ),
            "checks": checks,
            "anomaly_detection_results": anomaly_summary,
        }

        if export_report_path:
            try:
                report_path = Path(export_report_path)
                report_path.parent.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                with report_path.open("w", encoding="utf-8") as report_file:
                    json.dump(summary, report_file, indent=2)

            except (OSError, TypeError, ValueError):
                logger.exception(
                    "Could not write validation summary to %s",
                    export_report_path,
                )

        return summary