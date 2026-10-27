
import logging
from typing import List

from sqlalchemy.orm import Session

from src.models import (
    Application,
    JobRequisition,
    Interview,
    Feedback,
    InterviewerAssignment,
    ApplicationEvent,
    ApplicationStage,
    InterviewStatus,
    RequisitionStatus,
    RecommendationEnum,
    utc_now,
)

logger = logging.getLogger("recruitment_system.workflow")


class WorkflowError(Exception):
    """Raised when a lifecycle transition or prerequisite is invalid."""


PERMITTED_TRANSITIONS = {
    ApplicationStage.APPLIED: {
        ApplicationStage.SCREENING,
        ApplicationStage.WITHDRAWN,
    },
    ApplicationStage.SCREENING: {
        ApplicationStage.INTERVIEW,
        ApplicationStage.REJECTED,
        ApplicationStage.WITHDRAWN,
    },
    ApplicationStage.INTERVIEW: {
        ApplicationStage.DECISION_PENDING,
        ApplicationStage.REJECTED,
        ApplicationStage.WITHDRAWN,
    },
    ApplicationStage.DECISION_PENDING: {
    ApplicationStage.OFFER_PENDING_APPROVAL,
    ApplicationStage.OFFERED,
    ApplicationStage.REJECTED,
    ApplicationStage.WITHDRAWN,
    },
    ApplicationStage.OFFER_PENDING_APPROVAL: {
        ApplicationStage.OFFERED,
        ApplicationStage.REJECTED,
        ApplicationStage.WITHDRAWN,
    },
    ApplicationStage.OFFERED: {
        ApplicationStage.ACCEPTED,
        ApplicationStage.OFFER_REJECTED,
        ApplicationStage.OFFER_EXPIRED,
        ApplicationStage.WITHDRAWN,
    },
    ApplicationStage.ACCEPTED: set(),
    ApplicationStage.REJECTED: set(),
    ApplicationStage.WITHDRAWN: set(),
    ApplicationStage.OFFER_REJECTED: set(),
    ApplicationStage.OFFER_EXPIRED: set(),
}


class WorkflowEngine:
    """Manage candidate lifecycle transitions and interview feedback."""

    @classmethod
    def submit_feedback(
        cls,
        db: Session,
        interview_id: str,
        interviewer_id: str,
        technical_rating: int,
        communication_rating: int,
        problem_solving_rating: int,
        recommendation: RecommendationEnum,
        notes: str,
    ) -> Feedback:
        """Submit or revise feedback with rating validation and version tracking."""
        if not interview_id or not interview_id.strip():
            raise WorkflowError("Interview ID is required.")

        if not interviewer_id or not interviewer_id.strip():
            raise WorkflowError("Interviewer ID is required.")

        ratings = {
            "technical_rating": technical_rating,
            "communication_rating": communication_rating,
            "problem_solving_rating": problem_solving_rating,
        }

        for name, value in ratings.items():
            if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 5:
                raise WorkflowError(
                    f"Feedback rating '{name}' must be an integer between 1 and 5."
                )

        if not notes or not notes.strip():
            raise WorkflowError(
                "Feedback submission requires non-empty evaluation notes."
            )

        try:
            interview = (
                db.query(Interview)
                .filter(Interview.interview_id == interview_id)
                .first()
            )
            if interview is None:
                raise WorkflowError(
                    f"Interview '{interview_id}' not found."
                )

            if interview.status == InterviewStatus.CANCELLED:
                raise WorkflowError(
                    "Feedback cannot be submitted for a cancelled interview."
                )

            assignment = (
                db.query(InterviewerAssignment)
                .filter(
                    InterviewerAssignment.interview_id == interview_id,
                    InterviewerAssignment.interviewer_id == interviewer_id,
                )
                .first()
            )

            if assignment is None:
                raise WorkflowError(
                    f"Interviewer '{interviewer_id}' is not assigned to "
                    f"interview '{interview_id}'."
                )

            overall_score = round(
                technical_rating * 0.40
                + communication_rating * 0.30
                + problem_solving_rating * 0.30,
                2,
            )

            feedback_id = f"FB-{interview_id}-{interviewer_id}"
            feedback = (
                db.query(Feedback)
                .filter(Feedback.feedback_id == feedback_id)
                .first()
            )

            now = utc_now()

            if feedback is not None:
                feedback.technical_rating = technical_rating
                feedback.communication_rating = communication_rating
                feedback.problem_solving_rating = problem_solving_rating
                feedback.overall_score = overall_score
                feedback.recommendation = recommendation
                feedback.notes = notes.strip()
                feedback.version += 1
                feedback.updated_at = now
            else:
                feedback = Feedback(
                    feedback_id=feedback_id,
                    interview_id=interview_id,
                    interviewer_id=interviewer_id,
                    technical_rating=technical_rating,
                    communication_rating=communication_rating,
                    problem_solving_rating=problem_solving_rating,
                    overall_score=overall_score,
                    recommendation=recommendation,
                    notes=notes.strip(),
                    version=1,
                    submitted_at=now,
                    updated_at=now,
                )
                db.add(feedback)
                db.flush()

            # Mark complete only after every assigned interviewer has submitted feedback.
            assignments = (
                db.query(InterviewerAssignment)
                .filter(
                    InterviewerAssignment.interview_id == interview_id
                )
                .all()
            )

            feedback_by_interviewer = {
                item.interviewer_id
                for item in db.query(Feedback)
                .filter(Feedback.interview_id == interview_id)
                .all()
            }

            all_feedback_received = bool(assignments) and all(
                item.interviewer_id in feedback_by_interviewer
                for item in assignments
            )

            if (
                all_feedback_received
                and interview.status
                in (InterviewStatus.SCHEDULED, InterviewStatus.RESCHEDULED)
            ):
                interview.status = InterviewStatus.COMPLETED
                interview.updated_at = now

            db.commit()
            db.refresh(feedback)

            logger.info(
                "Feedback saved for interview %s by interviewer %s",
                interview_id,
                interviewer_id,
            )
            return feedback

        except Exception:
            db.rollback()
            raise

    @classmethod
    def check_missing_feedback(
        cls,
        db: Session,
        application_id: str,
    ) -> List[str]:
        """Return missing feedback entries for interviews associated with an application."""
        interviews = (
            db.query(Interview)
            .filter(
                Interview.application_id == application_id,
                Interview.status.in_(
                    [
                        InterviewStatus.SCHEDULED,
                        InterviewStatus.RESCHEDULED,
                        InterviewStatus.COMPLETED,
                    ]
                ),
            )
            .all()
        )

        missing = []

        for interview in interviews:
            assignments = (
                db.query(InterviewerAssignment)
                .filter(
                    InterviewerAssignment.interview_id
                    == interview.interview_id
                )
                .all()
            )

            submitted_ids = {
                item.interviewer_id
                for item in db.query(Feedback)
                .filter(Feedback.interview_id == interview.interview_id)
                .all()
            }

            for assignment in assignments:
                if assignment.interviewer_id not in submitted_ids:
                    missing.append(
                        f"Interview {interview.interview_id} missing feedback "
                        f"from {assignment.interviewer_id}"
                    )

        return missing

    @classmethod
    def transition_stage(
        cls,
        db: Session,
        application_id: str,
        target_stage: ApplicationStage,
        actor: str = "WORKFLOW_COORDINATOR",
        reason: str = "Stage transition",
        rule_version: str = "1.0",
        bypass_feedback_check: bool = False,
        bypass_role_status_check: bool = False,
    ) -> Application:
        """Validate prerequisites, transition application stage, and log the event."""
        if not application_id or not application_id.strip():
            raise WorkflowError("Application ID is required.")

        if not actor or not actor.strip():
            raise WorkflowError("Actor is required.")

        if not reason or len(reason.strip()) < 3:
            raise WorkflowError(
                "Transition reason must contain at least 3 characters."
            )

        if not rule_version or not rule_version.strip():
            raise WorkflowError("Rule version is required.")

        try:
            application = (
                db.query(Application)
                .filter(Application.application_id == application_id)
                .first()
            )

            if application is None:
                raise WorkflowError(
                    f"Application '{application_id}' not found."
                )

            current_stage = application.current_stage

            requisition = (
                db.query(JobRequisition)
                .filter(
                    JobRequisition.requisition_id
                    == application.requisition_id
                )
                .first()
            )

            if requisition is None:
                raise WorkflowError(
                    f"Requisition '{application.requisition_id}' "
                    "associated with the application was not found."
                )

            if not bypass_role_status_check and requisition.status in (
                RequisitionStatus.CLOSED,
                RequisitionStatus.CANCELLED,
            ):
                raise WorkflowError(
                    f"Cannot advance application '{application_id}': "
                    f"associated requisition '{requisition.requisition_id}' "
                    f"is {requisition.status.value}."
                )

            allowed_targets = PERMITTED_TRANSITIONS.get(
                current_stage, set()
            )

            if target_stage not in allowed_targets:
                permitted = sorted(
                    stage.value for stage in allowed_targets
                )
                raise WorkflowError(
                    f"Invalid stage transition: '{current_stage.value}' "
                    f"-> '{target_stage.value}'. "
                    f"Permitted next stages: {permitted}"
                )

            if (
                target_stage == ApplicationStage.DECISION_PENDING
                and not bypass_feedback_check
            ):
                missing_feedback = cls.check_missing_feedback(
                    db, application_id
                )
                if missing_feedback:
                    raise WorkflowError(
                        f"Cannot advance to DECISION_PENDING for application "
                        f"'{application_id}'. Missing required feedback: "
                        f"{'; '.join(missing_feedback)}"
                    )

            if (
                target_stage == ApplicationStage.INTERVIEW
                and not bypass_feedback_check
            ):
                if (
                    application.screening_score is not None
                    and application.screening_score < 70.0
                ):
                    raise WorkflowError(
                        f"Candidate failed screening with score "
                        f"{application.screening_score:.1f} "
                        "(Threshold: 70.0). Cannot advance to INTERVIEW."
                    )

            now = utc_now()
            application.current_stage = target_stage
            application.updated_at = now
            application.decision_reason = reason.strip()

            event = ApplicationEvent(
                application_id=application.application_id,
                from_stage=current_stage.value,
                to_stage=target_stage.value,
                actor=actor.strip(),
                reason=reason.strip(),
                rule_version=rule_version.strip(),
                event_timestamp=now,
            )
            db.add(event)

            db.commit()
            db.refresh(application)

            logger.info(
                "Application %s transitioned from %s to %s",
                application_id,
                current_stage.value,
                target_stage.value,
            )
            return application

        except Exception:
            db.rollback()
            raise
