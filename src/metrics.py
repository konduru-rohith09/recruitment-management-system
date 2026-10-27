
import logging
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from src.models import (
    JobRequisition,
    Application,
    Interview,
    Feedback,
    Offer,
    InterviewerAssignment,
    CandidateScreeningResult,
    AnomalyRecord,
    ApplicationStage,
    InterviewStatus,
    OfferStatus,
)

logger = logging.getLogger("recruitment_system.metrics")


class MetricsCalculator:
    """Calculate recruitment KPIs from persisted database records."""

    @classmethod
    def compute_all_metrics(
        cls,
        db: Session,
        department_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Calculate recruitment metrics, optionally filtered by department."""

        if department_id is not None and department_id <= 0:
            raise ValueError("Department ID must be a positive integer.")

        # 1. Requisitions by status
        req_query = db.query(JobRequisition)

        if department_id is not None:
            req_query = req_query.filter(
                JobRequisition.department_id == department_id
            )

        requisitions = req_query.all()
        total_requisitions = len(requisitions)

        requisitions_by_status: Dict[str, int] = {}

        for requisition in requisitions:
            status_value = requisition.status.value
            requisitions_by_status[status_value] = (
                requisitions_by_status.get(status_value, 0) + 1
            )

        # 2. Applications by stage
        app_query = db.query(Application).join(
            JobRequisition,
            Application.requisition_id
            == JobRequisition.requisition_id,
        )

        if department_id is not None:
            app_query = app_query.filter(
                JobRequisition.department_id == department_id
            )

        applications = app_query.all()
        total_applications = len(applications)

        applications_by_stage: Dict[str, int] = {}

        for application in applications:
            stage_value = application.current_stage.value
            applications_by_stage[stage_value] = (
                applications_by_stage.get(stage_value, 0) + 1
            )

        # 3. Screening metrics
        screening_query = db.query(CandidateScreeningResult)

        if department_id is not None:
            screening_query = screening_query.join(
                Application,
                CandidateScreeningResult.application_id
                == Application.application_id,
            ).join(
                JobRequisition,
                Application.requisition_id
                == JobRequisition.requisition_id,
            ).filter(
                JobRequisition.department_id == department_id
            )

        all_screening_results = screening_query.all()

        # Use only the latest screening evaluation for each application.
        # Older evaluations remain in the database as historical records.
        latest_by_application = {}

        for result in all_screening_results:
            current = latest_by_application.get(result.application_id)

            if current is None or (
                result.evaluated_at,
                result.id,
            ) > (
                current.evaluated_at,
                current.id,
            ):
                latest_by_application[result.application_id] = result

        screening_results = list(latest_by_application.values())
        total_screened = len(screening_results)

        passed_screening = sum(
            1
            for result in screening_results
            if (
                result.decision.value
                if hasattr(result.decision, "value")
                else str(result.decision)
            ).upper() == "PASS"
        )

        screening_pass_rate = (
            round(passed_screening / total_screened * 100.0, 2)
            if total_screened
            else 0.0
        )

        screening_scores = [
            result.final_score
            for result in screening_results
            if result.final_score is not None
        ]

        avg_screening_score = (
            round(sum(screening_scores) / len(screening_scores), 2)
            if screening_scores
            else 0.0
        )

        # 4. Interview metrics
        interview_query = db.query(Interview).join(
            Application,
            Interview.application_id == Application.application_id,
        ).join(
            JobRequisition,
            Application.requisition_id
            == JobRequisition.requisition_id,
        )

        if department_id is not None:
            interview_query = interview_query.filter(
                JobRequisition.department_id == department_id
            )

        interviews = interview_query.all()
        total_interviews = len(interviews)

        completed_interviews = sum(
            1
            for interview in interviews
            if interview.status == InterviewStatus.COMPLETED
        )
        cancelled_interviews = sum(
            1
            for interview in interviews
            if interview.status == InterviewStatus.CANCELLED
        )

        interview_completion_rate = (
            round(
                completed_interviews / total_interviews * 100.0,
                2,
            )
            if total_interviews
            else 0.0
        )

        # 5. Feedback completion rate
        assignment_query = db.query(InterviewerAssignment).join(
            Interview,
            InterviewerAssignment.interview_id == Interview.interview_id,
        ).join(
            Application,
            Interview.application_id == Application.application_id,
        ).join(
            JobRequisition,
            Application.requisition_id
            == JobRequisition.requisition_id,
        )

        feedback_query = db.query(Feedback).join(
            Interview,
            Feedback.interview_id == Interview.interview_id,
        ).join(
            Application,
            Interview.application_id == Application.application_id,
        ).join(
            JobRequisition,
            Application.requisition_id
            == JobRequisition.requisition_id,
        )

        if department_id is not None:
            assignment_query = assignment_query.filter(
                JobRequisition.department_id == department_id
            )
            feedback_query = feedback_query.filter(
                JobRequisition.department_id == department_id
            )

        total_assignments = assignment_query.count()
        submitted_feedbacks = feedback_query.count()

        feedback_completion_rate = (
            round(
                min(submitted_feedbacks, total_assignments)
                / total_assignments
                * 100.0,
                2,
            )
            if total_assignments
            else 0.0
        )

        # 6. Offer metrics
        offer_query = db.query(Offer).join(
            Application,
            Offer.application_id == Application.application_id,
        ).join(
            JobRequisition,
            Application.requisition_id
            == JobRequisition.requisition_id,
        )

        if department_id is not None:
            offer_query = offer_query.filter(
                JobRequisition.department_id == department_id
            )

        offers = offer_query.all()
        total_offers = len(offers)

        accepted_offers = sum(
            1 for offer in offers
            if offer.status == OfferStatus.ACCEPTED
        )
        rejected_offers = sum(
            1 for offer in offers
            if offer.status == OfferStatus.REJECTED
        )
        expired_offers = sum(
            1 for offer in offers
            if offer.status == OfferStatus.EXPIRED
        )

        decided_offers = (
            accepted_offers + rejected_offers + expired_offers
        )

        offer_acceptance_rate = (
            round(
                accepted_offers / decided_offers * 100.0,
                2,
            )
            if decided_offers
            else 0.0
        )

        # 7. Withdrawal and rejection rates
        withdrawn_apps = sum(
            1
            for application in applications
            if application.current_stage == ApplicationStage.WITHDRAWN
        )

        rejected_stages = {
            ApplicationStage.REJECTED,
            ApplicationStage.OFFER_REJECTED,
        }

        rejected_apps = sum(
            1
            for application in applications
            if application.current_stage in rejected_stages
        )

        withdrawal_rate = (
            round(withdrawn_apps / total_applications * 100.0, 2)
            if total_applications
            else 0.0
        )

        rejection_rate = (
            round(rejected_apps / total_applications * 100.0, 2)
            if total_applications
            else 0.0
        )

        # 8. Average time to decision
        terminal_stages = {
            ApplicationStage.ACCEPTED,
            ApplicationStage.REJECTED,
            ApplicationStage.OFFER_REJECTED,
            ApplicationStage.OFFER_EXPIRED,
        }

        decided_applications = [
            application
            for application in applications
            if (
                application.current_stage in terminal_stages
                and application.applied_at is not None
                and application.updated_at is not None
            )
        ]

        decision_durations = [
            max(
                0.0,
                (
                    application.updated_at - application.applied_at
                ).total_seconds()
                / 86400.0,
            )
            for application in decided_applications
        ]

        avg_time_to_decision_days = (
            round(
                sum(decision_durations) / len(decision_durations),
                1,
            )
            if decision_durations
            else 0.0
        )

        # 9. Anomaly summary
        anomaly_query = db.query(AnomalyRecord)

        if department_id is not None:
            # Anomaly records do not have a reliable department foreign key.
            # Keep the anomaly summary global rather than misattribute records.
            logger.debug(
                "Anomaly summary is global; department filter %s "
                "cannot be reliably applied.",
                department_id,
            )

        anomalies = anomaly_query.all()

        anomalies_by_type: Dict[str, int] = {}
        anomalies_by_severity: Dict[str, int] = {}

        for anomaly in anomalies:
            anomalies_by_type[anomaly.issue_type] = (
                anomalies_by_type.get(anomaly.issue_type, 0) + 1
            )

            severity_value = (
                anomaly.severity.value
                if hasattr(anomaly.severity, "value")
                else str(anomaly.severity)
            )

            anomalies_by_severity[severity_value] = (
                anomalies_by_severity.get(severity_value, 0) + 1
            )

        return {
            "overview": {
                "total_requisitions": total_requisitions,
                "total_applications": total_applications,
                "total_interviews": total_interviews,
                "total_offers": total_offers,
            },
            "requisitions_by_status": requisitions_by_status,
            "applications_by_stage": applications_by_stage,
            "screening": {
                "total_screened": total_screened,
                "passed_screening": passed_screening,
                "screening_pass_rate_pct": screening_pass_rate,
                "average_screening_score": avg_screening_score,
            },
            "interviews": {
                "total_interviews": total_interviews,
                "completed_interviews": completed_interviews,
                "cancelled_interviews": cancelled_interviews,
                "interview_completion_rate_pct": interview_completion_rate,
                "feedback_completion_rate_pct": feedback_completion_rate,
            },
            "offers": {
                "total_offers": total_offers,
                "decided_offers": decided_offers,
                "accepted_offers": accepted_offers,
                "rejected_offers": rejected_offers,
                "expired_offers": expired_offers,
                "offer_acceptance_rate_pct": offer_acceptance_rate,
            },
            "funnel_rates": {
                "withdrawal_rate_pct": withdrawal_rate,
                "rejection_rate_pct": rejection_rate,
                "avg_time_to_decision_days": avg_time_to_decision_days,
            },
            "anomalies": {
                "total_cou.venv\Scripts\python.exe -m pytest tests\test_validation.py -qnt": len(anomalies),
                "by_type": anomalies_by_type,
                "by_severity": anomalies_by_severity,
            },
        }
