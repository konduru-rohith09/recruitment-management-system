import json
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.models import (
    Application,
    ApplicationStage,
    AnomalyDetectionResult,
    AnomalyRecord,
    AnomalySeverity,
    AuditEvent,
    DuplicateApplicationAttempt,
    Feedback,
    Interview,
    InterviewStatus,
    Interviewer,
    InterviewerAssignment,
    JobRequisition,
    Offer,
    RequisitionStatus,
    utc_now,
)

logger = logging.getLogger("recruitment_system.audit")


class AuditService:
    """Manage audit logging and compliance anomaly detection."""

    @classmethod
    def log_audit(
        cls,
        db: Session,
        entity_type: str,
        entity_id: str,
        action: str,
        actor: str,
        previous_state: Optional[Dict[str, Any]] = None,
        new_state: Optional[Dict[str, Any]] = None,
        reason: Optional[str] = None,
    ) -> AuditEvent:
        """Append an audit event to the audit ledger."""
        values = {
            "Entity type": entity_type,
            "Entity ID": entity_id,
            "Audit action": action,
            "Audit actor": actor,
        }

        for label, value in values.items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{label} is required.")

        event = AuditEvent(
            entity_type=entity_type.strip(),
            entity_id=entity_id.strip(),
            action=action.strip(),
            previous_state_json=(
                json.dumps(previous_state, default=str)
                if previous_state is not None
                else None
            ),
            new_state_json=(
                json.dumps(new_state, default=str)
                if new_state is not None
                else None
            ),
            actor=actor.strip(),
            timestamp=utc_now(),
            reason=reason.strip() if reason and reason.strip() else None,
        )

        try:
            db.add(event)
            db.commit()
            db.refresh(event)
            return event
        except Exception:
            db.rollback()
            logger.exception("Failed to record audit event")
            raise

    @classmethod
    def record_anomaly(
        cls,
        db: Session,
        issue_id: str,
        issue_type: str,
        affected_entity_type: str,
        affected_record_id: str,
        expected_decision: str,
        severity: AnomalySeverity,
        detection_result: AnomalyDetectionResult,
        explanation: str,
        recommended_action: str,
    ) -> AnomalyRecord:
        """Create or update an anomaly record using its stable issue ID."""
        required_values = {
            "Anomaly issue ID": issue_id,
            "Anomaly issue type": issue_type,
            "Affected entity type": affected_entity_type,
            "Affected record ID": affected_record_id,
            "Expected decision": expected_decision,
            "Explanation": explanation,
            "Recommended action": recommended_action,
        }

        for label, value in required_values.items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{label} is required.")

        if not isinstance(severity, AnomalySeverity):
            raise ValueError("Invalid anomaly severity.")

        if not isinstance(detection_result, AnomalyDetectionResult):
            raise ValueError("Invalid anomaly detection result.")

        try:
            record = db.get(AnomalyRecord, issue_id.strip())

            if record is None:
                record = AnomalyRecord(
                    issue_id=issue_id.strip(),
                    issue_type=issue_type.strip(),
                    affected_entity_type=affected_entity_type.strip(),
                    affected_record_id=affected_record_id.strip(),
                    expected_decision=expected_decision.strip(),
                    severity=severity,
                    detection_result=detection_result,
                    explanation=explanation.strip(),
                    recommended_action=recommended_action.strip(),
                    detected_at=utc_now(),
                )
                db.add(record)
            else:
                record.issue_type = issue_type.strip()
                record.affected_entity_type = affected_entity_type.strip()
                record.affected_record_id = affected_record_id.strip()
                record.expected_decision = expected_decision.strip()
                record.severity = severity
                record.detection_result = detection_result
                record.explanation = explanation.strip()
                record.recommended_action = recommended_action.strip()

            db.commit()
            db.refresh(record)
            return record

        except Exception:
            db.rollback()
            logger.exception("Failed to record anomaly %s", issue_id)
            raise

    @classmethod
    def scan_for_anomalies(
        cls,
        db: Session,
    ) -> List[AnomalyRecord]:
        """
        Detect five compliance scenarios:
        1. Interviewer unavailable or overlapping interviews.
        2. Duplicate application attempts or records.
        3. Missing interview feedback.
        4. Offers outside the approved salary band.
        5. Active applications under closed requisitions.
        """
        detected_anomalies: List[AnomalyRecord] = []

        def add_anomaly(
            issue_id: str,
            issue_type: str,
            affected_entity_type: str,
            affected_record_id: str,
            expected_decision: str,
            severity: AnomalySeverity,
            detection_result: AnomalyDetectionResult,
            explanation: str,
            recommended_action: str,
        ) -> None:
            record = cls.record_anomaly(
                db=db,
                issue_id=issue_id,
                issue_type=issue_type,
                affected_entity_type=affected_entity_type,
                affected_record_id=affected_record_id,
                expected_decision=expected_decision,
                severity=severity,
                detection_result=detection_result,
                explanation=explanation,
                recommended_action=recommended_action,
            )
            detected_anomalies.append(record)

        active_interview_statuses = [
            InterviewStatus.SCHEDULED,
            InterviewStatus.RESCHEDULED,
            InterviewStatus.COMPLETED,
        ]

        # 1. Interviewer availability and overlapping interviews.
        assignments = (
            db.query(InterviewerAssignment, Interview, Interviewer)
            .join(
                Interview,
                InterviewerAssignment.interview_id == Interview.interview_id,
            )
            .join(
                Interviewer,
                InterviewerAssignment.interviewer_id
                == Interviewer.interviewer_id,
            )
            .filter(Interview.status.in_(active_interview_statuses))
            .all()
        )

        for assignment, interview, interviewer in assignments:
            if not interviewer.is_active:
                add_anomaly(
                    issue_id=(
                        f"ANOM-INACTIVE-{interview.interview_id}-"
                        f"{interviewer.interviewer_id}"
                    ),
                    issue_type="INTERVIEWER_UNAVAILABLE",
                    affected_entity_type="INTERVIEW",
                    affected_record_id=interview.interview_id,
                    expected_decision="BLOCK_ASSIGNMENT_OR_RESCHEDULE",
                    severity=AnomalySeverity.HIGH,
                    detection_result=(
                        AnomalyDetectionResult.DETECTED_IN_AUDIT
                    ),
                    explanation=(
                        f"Interview {interview.interview_id} is assigned "
                        f"to inactive interviewer {interviewer.interviewer_id} "
                        f"({interviewer.name})."
                    ),
                    recommended_action=(
                        f"Reassign interview {interview.interview_id} "
                        "to an active interviewer."
                    ),
                )

            overlaps = (
                db.query(Interview)
                .join(
                    InterviewerAssignment,
                    Interview.interview_id
                    == InterviewerAssignment.interview_id,
                )
                .filter(
                    InterviewerAssignment.interviewer_id
                    == interviewer.interviewer_id,
                    Interview.interview_id != interview.interview_id,
                    Interview.status.in_(active_interview_statuses),
                    Interview.scheduled_start < interview.scheduled_end,
                    Interview.scheduled_end > interview.scheduled_start,
                )
                .all()
            )

            for other in overlaps:
                first_id, second_id = sorted(
                    [interview.interview_id, other.interview_id]
                )

                add_anomaly(
                    issue_id=(
                        f"ANOM-OVERLAP-{first_id}-{second_id}-"
                        f"{interviewer.interviewer_id}"
                    ),
                    issue_type="INTERVIEWER_UNAVAILABLE",
                    affected_entity_type="INTERVIEW",
                    affected_record_id=f"{first_id},{second_id}",
                    expected_decision="PREVENT_OVERLAPPING_BOOKING",
                    severity=AnomalySeverity.CRITICAL,
                    detection_result=(
                        AnomalyDetectionResult.DETECTED_IN_AUDIT
                    ),
                    explanation=(
                        f"Interviewer {interviewer.interviewer_id} has "
                        f"overlapping interviews {first_id} and {second_id}."
                    ),
                    recommended_action="Reschedule one conflicting interview.",
                )

        # 2. Duplicate application attempts.
        duplicate_attempts = db.query(DuplicateApplicationAttempt).all()

        for attempt in duplicate_attempts:
            add_anomaly(
                issue_id=f"ANOM-DUP-ATTEMPT-{attempt.attempt_id}",
                issue_type="DUPLICATE_APPLICATION",
                affected_entity_type="APPLICATION",
                affected_record_id=attempt.attempt_id,
                expected_decision="REJECT_OR_FLAG_DUPLICATE_ATTEMPT",
                severity=AnomalySeverity.MEDIUM,
                detection_result=(
                    AnomalyDetectionResult.BLOCKED_BY_VALIDATION
                ),
                explanation=(
                    f"Duplicate attempt {attempt.attempt_id} by candidate "
                    f"{attempt.candidate_id} for requisition "
                    f"{attempt.requisition_id} was preserved for auditing."
                ),
                recommended_action=(
                    "Preserve the duplicate-attempt audit record."
                ),
            )

        # Detect duplicate application records if database constraints
        # were bypassed or changed.
        duplicate_groups = (
            db.query(
                Application.candidate_id,
                Application.requisition_id,
                func.count(Application.application_id).label("total"),
            )
            .group_by(
                Application.candidate_id,
                Application.requisition_id,
            )
            .having(func.count(Application.application_id) > 1)
            .all()
        )

        for candidate_id, requisition_id, count in duplicate_groups:
            application_ids = sorted(
                row.application_id
                for row in db.query(Application)
                .filter(
                    Application.candidate_id == candidate_id,
                    Application.requisition_id == requisition_id,
                )
                .all()
            )

            add_anomaly(
                issue_id=(
                    f"ANOM-DUP-APPLICATION-{requisition_id}-{candidate_id}"
                ),
                issue_type="DUPLICATE_APPLICATION",
                affected_entity_type="APPLICATION",
                affected_record_id=";".join(application_ids),
                expected_decision="REJECT_OR_FLAG_DUPLICATE_ATTEMPT",
                severity=AnomalySeverity.MEDIUM,
                detection_result=(
                    AnomalyDetectionResult.DETECTED_IN_AUDIT
                ),
                explanation=(
                    f"Candidate {candidate_id} submitted {count} "
                    f"applications for requisition {requisition_id}: "
                    f"{'; '.join(application_ids)}."
                ),
                recommended_action=(
                    "Investigate duplicate records and preserve audit evidence."
                ),
            )

        # 3. Missing interview feedback for advanced applications.
        advanced_stages = [
            ApplicationStage.DECISION_PENDING,
            ApplicationStage.OFFER_PENDING_APPROVAL,
            ApplicationStage.OFFERED,
            ApplicationStage.ACCEPTED,
        ]

        advanced_applications = (
            db.query(Application)
            .filter(Application.current_stage.in_(advanced_stages))
            .all()
        )

        for application in advanced_applications:
            interviews = (
                db.query(Interview)
                .filter(
                    Interview.application_id == application.application_id,
                )
                .all()
            )

            for interview in interviews:
                # Cancelled interviews should not require feedback.
                if interview.status == InterviewStatus.CANCELLED:
                    continue

                assignments = (
                    db.query(InterviewerAssignment)
                    .filter(
                        InterviewerAssignment.interview_id
                        == interview.interview_id,
                    )
                    .all()
                )

                submitted_ids = {
                    row.interviewer_id
                    for row in db.query(Feedback.interviewer_id)
                    .filter(Feedback.interview_id == interview.interview_id)
                    .all()
                }

                for assignment in assignments:
                    if assignment.interviewer_id in submitted_ids:
                        continue

                    add_anomaly(
                        issue_id=(
                            f"ANOM-MISSING-FEEDBACK-{interview.interview_id}-"
                            f"{assignment.interviewer_id}"
                        ),
                        issue_type="MISSING_FEEDBACK",
                        affected_entity_type="APPLICATION",
                        affected_record_id=application.application_id,
                        expected_decision=(
                            "BLOCK_ADVANCEMENT_UNTIL_FEEDBACK_SUBMITTED"
                        ),
                        severity=AnomalySeverity.HIGH,
                        detection_result=(
                            AnomalyDetectionResult.DETECTED_IN_AUDIT
                        ),
                        explanation=(
                            f"Application {application.application_id} "
                            f"advanced to {application.current_stage.value} "
                            f"without feedback from interviewer "
                            f"{assignment.interviewer_id} for interview "
                            f"{interview.interview_id}."
                        ),
                        recommended_action=(
                            "Collect missing feedback and review the "
                            "application's stage transition."
                        ),
                    )

        # 4. Offers outside the requisition salary band.
        offers = (
            db.query(Offer, Application, JobRequisition)
            .join(
                Application,
                Offer.application_id == Application.application_id,
            )
            .join(
                JobRequisition,
                Application.requisition_id == JobRequisition.requisition_id,
            )
            .all()
        )

        for offer, application, requisition in offers:
            outside_band = (
                offer.base_salary < requisition.min_salary
                or offer.base_salary > requisition.max_salary
            )

            if outside_band and not offer.exception_approved_by:
                add_anomaly(
                    issue_id=f"ANOM-SALARY-{offer.offer_id}",
                    issue_type="SALARY_OUTSIDE_BAND",
                    affected_entity_type="OFFER",
                    affected_record_id=offer.offer_id,
                    expected_decision=(
                        "BLOCK_OFFER_OR_REQUIRE_EXECUTIVE_APPROVAL"
                    ),
                    severity=AnomalySeverity.HIGH,
                    detection_result=(
                        AnomalyDetectionResult.DETECTED_IN_AUDIT
                    ),
                    explanation=(
                        f"Offer {offer.offer_id} salary "
                        f"{offer.currency} {offer.base_salary:,.2f} is "
                        f"outside requisition {requisition.requisition_id} "
                        f"band ({requisition.min_salary:,.2f}–"
                        f"{requisition.max_salary:,.2f}) without an "
                        "approved exception."
                    ),
                    recommended_action=(
                        "Obtain authorized compensation approval or adjust "
                        "the offer to the approved salary band."
                    ),
                )

        # 5. Active applications under closed or cancelled requisitions.
        active_application_stages = [
            ApplicationStage.APPLIED,
            ApplicationStage.SCREENING,
            ApplicationStage.INTERVIEW,
            ApplicationStage.DECISION_PENDING,
            ApplicationStage.OFFER_PENDING_APPROVAL,
            ApplicationStage.OFFERED,
        ]

        closed_role_applications = (
            db.query(Application, JobRequisition)
            .join(
                JobRequisition,
                Application.requisition_id == JobRequisition.requisition_id,
            )
            .filter(
                JobRequisition.status.in_(
                    [
                        RequisitionStatus.CLOSED,
                        RequisitionStatus.CANCELLED,
                    ]
                ),
                Application.current_stage.in_(active_application_stages),
            )
            .all()
        )

        for application, requisition in closed_role_applications:
            add_anomaly(
                issue_id=(
                    f"ANOM-CLOSED-ROLE-{requisition.requisition_id}-"
                    f"{application.application_id}"
                ),
                issue_type="CLOSED_ROLE_ACTIVE_APPLICATIONS",
                affected_entity_type="APPLICATION",
                affected_record_id=application.application_id,
                expected_decision=(
                    "DISPOSITION_APPLICATIONS_BEFORE_CLOSING_REQUISITION"
                ),
                severity=AnomalySeverity.MEDIUM,
                detection_result=(
                    AnomalyDetectionResult.DETECTED_IN_AUDIT
                ),
                explanation=(
                    f"Application {application.application_id} remains "
                    f"active in stage '{application.current_stage.value}' "
                    f"under {requisition.status.value} requisition "
                    f"{requisition.requisition_id}."
                ),
                recommended_action=(
                    f"Disposition application {application.application_id} "
                    "to REJECTED or WITHDRAWN."
                ),
            )

        return detected_anomalies