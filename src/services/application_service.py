
import logging
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from src.models import (
    Application,
    Candidate,
    JobRequisition,
    ApplicationStage,
    RequisitionStatus,
    ApplicationEvent,
    utc_now,
)
from src.screening import ScreeningEngine
from src.workflow import WorkflowEngine
from src.audit import AuditService

logger = logging.getLogger("recruitment_system.application_service")


class ApplicationService:
    """Manage application submissions, screening, and stage progression."""

    @classmethod
    def generate_application_id(
        cls, requisition_id: str, candidate_id: str
    ) -> str:
        """Generate a deterministic application ID."""
        return f"APP-{requisition_id}-{candidate_id}"

    @classmethod
    def apply(
        cls,
        db: Session,
        candidate_id: str,
        requisition_id: str,
        actor: str = "CANDIDATE_PORTAL",
        allow_duplicate_anomaly: bool = False,
    ) -> Tuple[Optional[Application], Dict[str, Any]]:
        """Submit an application and prevent duplicate applications."""
        candidate_id = candidate_id.strip()
        requisition_id = requisition_id.strip()
        actor = actor.strip()

        if not candidate_id:
            raise ValueError("Candidate ID is required.")
        if not requisition_id:
            raise ValueError("Requisition ID is required.")
        if not actor:
            raise ValueError("Actor is required.")

        try:
            candidate = (
                db.query(Candidate)
                .filter(Candidate.candidate_id == candidate_id)
                .first()
            )
            if candidate is None:
                raise ValueError(
                    f"Candidate '{candidate_id}' does not exist."
                )

            requisition = (
                db.query(JobRequisition)
                .filter(
                    JobRequisition.requisition_id == requisition_id
                )
                .first()
            )
            if requisition is None:
                raise ValueError(
                    f"Job requisition '{requisition_id}' does not exist."
                )

            # Preserve the existing business rule allowing DRAFT applications.
            if requisition.status not in (
                RequisitionStatus.OPEN,
                RequisitionStatus.DRAFT,
            ):
                raise ValueError(
                    f"Cannot apply to requisition '{requisition_id}': "
                    f"Role is {requisition.status.value}."
                )

            app_id = cls.generate_application_id(
                requisition_id, candidate_id
            )

            existing_app = (
                db.query(Application)
                .filter(Application.application_id == app_id)
                .first()
            )

            if existing_app is not None:
                if not allow_duplicate_anomaly:
                    raise ValueError(
                        "Duplicate application blocked: "
                        f"Candidate '{candidate_id}' has already applied "
                        f"to requisition '{requisition_id}' "
                        f"(Application ID: {existing_app.application_id})."
                    )

                # Use a unique ID for each controlled anomaly attempt.
                duplicate_staging_id = (
                    f"{app_id}-DUP-ATTEMPT-{utc_now().strftime('%Y%m%d%H%M%S%f')}"
                )

                duplicate_app = Application(
                    application_id=duplicate_staging_id,
                    candidate_id=candidate_id,
                    requisition_id=requisition_id,
                    current_stage=ApplicationStage.APPLIED,
                    decision_reason="FLAGGED_DUPLICATE_APPLICATION_ATTEMPT",
                    applied_at=utc_now(),
                    updated_at=utc_now(),
                )
                db.add(duplicate_app)
                db.flush()

                AuditService.log_audit(
                    db=db,
                    entity_type="Application",
                    entity_id=duplicate_staging_id,
                    action="DUPLICATE_APPLICATION_ATTEMPT",
                    actor=actor,
                    new_state={
                        "candidate_id": candidate_id,
                        "requisition_id": requisition_id,
                        "stage": ApplicationStage.APPLIED.value,
                    },
                    reason="Controlled duplicate application anomaly",
                )

                db.commit()
                db.refresh(duplicate_app)

                return duplicate_app, {
                    "status": "FLAGGED_DUPLICATE",
                    "message": "Duplicate application recorded as a controlled anomaly.",
                }

            now = utc_now()
            new_app = Application(
                application_id=app_id,
                candidate_id=candidate_id,
                requisition_id=requisition_id,
                current_stage=ApplicationStage.APPLIED,
                applied_at=now,
                updated_at=now,
            )
            db.add(new_app)
            db.flush()

            event = ApplicationEvent(
                application_id=new_app.application_id,
                from_stage="NONE",
                to_stage=ApplicationStage.APPLIED.value,
                actor=actor,
                reason="Initial application lodgement",
                rule_version="1.0",
                event_timestamp=now,
            )
            db.add(event)

            AuditService.log_audit(
                db=db,
                entity_type="Application",
                entity_id=new_app.application_id,
                action="APPLY",
                actor=actor,
                new_state={
                    "candidate_id": candidate_id,
                    "requisition_id": requisition_id,
                    "stage": new_app.current_stage.value,
                },
                reason="Candidate application submitted",
            )

            db.commit()
            db.refresh(new_app)

            return new_app, {
                "status": "SUCCESS",
                "message": "Application lodged successfully.",
            }

        except Exception:
            db.rollback()
            raise

    @classmethod
    def screen_application(
        cls,
        db: Session,
        application_id: str,
        assessment_score: float = 75.0,
        actor: str = "SCREENING_SERVICE",
    ):
        """Evaluate an application against requisition screening criteria."""
        if not 0.0 <= assessment_score <= 100.0:
            raise ValueError(
                "Assessment score must be between 0 and 100."
            )
        if not application_id.strip():
            raise ValueError("Application ID is required.")
        if not actor.strip():
            raise ValueError("Actor is required.")

        return ScreeningEngine.evaluate_application(
            db=db,
            application_id=application_id,
            assessment_score=assessment_score,
            actor=actor,
        )

    @classmethod
    def transition_stage(
        cls,
        db: Session,
        application_id: str,
        target_stage: ApplicationStage,
        actor: str = "RECRUITER",
        reason: str = "Stage transition",
        rule_version: str = "1.0",
        bypass_feedback_check: bool = False,
        bypass_role_status_check: bool = False,
    ) -> Application:
        """Transition an application using the workflow engine."""
        if not application_id.strip():
            raise ValueError("Application ID is required.")
        if not actor.strip():
            raise ValueError("Actor is required.")
        if len(reason.strip()) < 3:
            raise ValueError(
                "Transition reason must contain at least 3 characters."
            )
        if not rule_version.strip():
            raise ValueError("Rule version is required.")

        return WorkflowEngine.transition_stage(
            db=db,
            application_id=application_id,
            target_stage=target_stage,
            actor=actor,
            reason=reason,
            rule_version=rule_version,
            bypass_feedback_check=bypass_feedback_check,
            bypass_role_status_check=bypass_role_status_check,
        )

    @classmethod
    def list_applications(
        cls,
        db: Session,
        requisition_id: Optional[str] = None,
        candidate_id: Optional[str] = None,
        stage: Optional[ApplicationStage] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[Application], int]:
        """List applications with filters and pagination."""
        if skip < 0:
            raise ValueError("Skip cannot be negative.")
        if limit < 1:
            raise ValueError("Limit must be at least 1.")

        query = db.query(Application)

        if requisition_id is not None:
            query = query.filter(
                Application.requisition_id == requisition_id
            )
        if candidate_id is not None:
            query = query.filter(
                Application.candidate_id == candidate_id
            )
        if stage is not None:
            query = query.filter(
                Application.current_stage == stage
            )

        total = query.count()
        items = (
            query.order_by(Application.applied_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        return items, total

    @classmethod
    def get_by_id(
        cls, db: Session, application_id: str
    ) -> Optional[Application]:
        """Retrieve an application by its ID."""
        return (
            db.query(Application)
            .filter(Application.application_id == application_id)
            .first()
        )
