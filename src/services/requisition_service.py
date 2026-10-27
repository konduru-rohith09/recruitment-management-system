
import logging
from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import desc
from sqlalchemy.orm import Session

from src.models import (
    JobRequisition,
    Department,
    RequisitionRequiredSkill,
    RequisitionApproval,
    RequisitionStatus,
    ApprovalStatus,
    Application,
    ApplicationStage,
    utc_now,
)
from src.audit import AuditService

logger = logging.getLogger("recruitment_system.requisition_service")


class RequisitionService:
    """Business logic for job requisitions."""

    @classmethod
    def generate_next_requisition_id(
        cls, db: Session, year: int = 2026
    ) -> str:
        """Generate an ID in the format REQ-YYYY-NNNNNN."""
        prefix = f"REQ-{year}-"

        last_req = (
            db.query(JobRequisition)
            .filter(JobRequisition.requisition_id.like(f"{prefix}%"))
            .order_by(desc(JobRequisition.requisition_id))
            .first()
        )

        sequence = 1
        if last_req:
            try:
                sequence = int(last_req.requisition_id.rsplit("-", 1)[-1]) + 1
            except (ValueError, AttributeError):
                logger.warning(
                    "Could not parse requisition ID %s; restarting sequence",
                    last_req.requisition_id,
                )

        return f"{prefix}{sequence:06d}"

    @classmethod
    def create_requisition(
        cls,
        db: Session,
        title: str,
        department_id: int,
        hiring_manager_id: str,
        min_salary: float,
        max_salary: float,
        headcount: int = 1,
        min_experience_years: float = 0.0,
        currency: str = "USD",
        location: str = "Remote",
        required_skill_ids: Optional[List[int]] = None,
        custom_id: Optional[str] = None,
    ) -> JobRequisition:
        """Create a requisition in DRAFT status."""
        title = title.strip()
        hiring_manager_id = hiring_manager_id.strip()
        currency = currency.strip().upper()
        location = location.strip()

        if len(title) < 2:
            raise ValueError("Title must contain at least 2 characters.")
        if not hiring_manager_id:
            raise ValueError("Hiring manager ID is required.")
        if department_id <= 0:
            raise ValueError("Department ID must be positive.")
        if min_salary < 0 or max_salary < min_salary:
            raise ValueError(
                "Invalid salary band: minimum salary cannot exceed maximum salary."
            )
        if headcount < 1:
            raise ValueError("Headcount must be at least 1.")
        if min_experience_years < 0:
            raise ValueError("Minimum experience cannot be negative.")
        if len(currency) != 3:
            raise ValueError("Currency must be a three-character code.")
        if not location:
            raise ValueError("Location is required.")

        skill_ids = required_skill_ids or []
        if any(skill_id <= 0 for skill_id in skill_ids):
            raise ValueError("Skill IDs must be positive integers.")
        if len(skill_ids) != len(set(skill_ids)):
            raise ValueError("Duplicate required skill IDs are not allowed.")

        try:
            dept = (
                db.query(Department)
                .filter(Department.id == department_id)
                .first()
            )
            if dept is None:
                raise ValueError(
                    f"Department ID {department_id} does not exist."
                )

            req_id = custom_id or cls.generate_next_requisition_id(db)

            if (
                db.query(JobRequisition)
                .filter(JobRequisition.requisition_id == req_id)
                .first()
                is not None
            ):
                raise ValueError(f"Requisition ID '{req_id}' already exists.")

            now = utc_now()
            req = JobRequisition(
                requisition_id=req_id,
                title=title,
                department_id=department_id,
                hiring_manager_id=hiring_manager_id,
                status=RequisitionStatus.DRAFT,
                headcount=headcount,
                min_experience_years=min_experience_years,
                min_salary=min_salary,
                max_salary=max_salary,
                currency=currency,
                location=location,
                created_at=now,
                updated_at=now,
            )
            db.add(req)
            db.flush()

            for skill_id in skill_ids:
                db.add(
                    RequisitionRequiredSkill(
                        requisition_id=req.requisition_id,
                        skill_id=skill_id,
                        is_required=True,
                        min_experience_years=max(
                            1.0, min_experience_years * 0.5
                        ),
                    )
                )

            AuditService.log_audit(
                db=db,
                entity_type="JobRequisition",
                entity_id=req.requisition_id,
                action="CREATE",
                actor=hiring_manager_id,
                new_state={
                    "title": title,
                    "min_salary": min_salary,
                    "max_salary": max_salary,
                    "status": req.status.value,
                },
                reason="Requisition drafted",
            )

            db.commit()
            db.refresh(req)
            return req

        except Exception:
            db.rollback()
            raise

    @classmethod
    def open_requisition(
        cls, db: Session, requisition_id: str, approver_id: str
    ) -> JobRequisition:
        """Approve and open a requisition for talent acquisition."""
        approver_id = approver_id.strip()
        if not approver_id:
            raise ValueError("Approver ID is required.")

        try:
            req = (
                db.query(JobRequisition)
                .filter(JobRequisition.requisition_id == requisition_id)
                .first()
            )
            if req is None:
                raise ValueError(f"Requisition {requisition_id} not found.")

            if req.status != RequisitionStatus.DRAFT:
                raise ValueError(
                    f"Only DRAFT requisitions can be opened; current status is {req.status.value}."
                )

            now = utc_now()
            approval = RequisitionApproval(
                requisition_id=requisition_id,
                approver_id=approver_id,
                status=ApprovalStatus.APPROVED,
                decided_at=now,
                created_at=now,
            )
            db.add(approval)

            req.status = RequisitionStatus.OPEN
            req.opened_at = now
            req.updated_at = now

            AuditService.log_audit(
                db=db,
                entity_type="JobRequisition",
                entity_id=requisition_id,
                action="OPEN",
                actor=approver_id,
                new_state={
                    "status": req.status.value,
                    "opened_at": now.isoformat(),
                },
                reason="Requisition approved and opened",
            )

            db.commit()
            db.refresh(req)
            return req

        except Exception:
            db.rollback()
            raise

    @classmethod
    def close_requisition(
        cls,
        db: Session,
        requisition_id: str,
        actor: str = "HR_ADMIN",
        allow_active_applications: bool = False,
    ) -> JobRequisition:
        """Close a requisition after checking active applications."""
        actor = actor.strip()
        if not actor:
            raise ValueError("Actor is required.")

        try:
            req = (
                db.query(JobRequisition)
                .filter(JobRequisition.requisition_id == requisition_id)
                .first()
            )
            if req is None:
                raise ValueError(f"Requisition {requisition_id} not found.")

            if req.status == RequisitionStatus.CLOSED:
                raise ValueError(
                    f"Requisition {requisition_id} is already closed."
                )

            if not allow_active_applications:
                active_stages = [
                    ApplicationStage.APPLIED,
                    ApplicationStage.SCREENING,
                    ApplicationStage.INTERVIEW,
                    ApplicationStage.DECISION_PENDING,
                    ApplicationStage.OFFER_PENDING_APPROVAL,
                    ApplicationStage.OFFERED,
                ]

                active_count = (
                    db.query(Application)
                    .filter(
                        Application.requisition_id == requisition_id,
                        Application.current_stage.in_(active_stages),
                    )
                    .count()
                )

                if active_count > 0:
                    raise ValueError(
                        f"Cannot close requisition {requisition_id}: "
                        f"{active_count} active candidate applications exist. "
                        "Disposition them first."
                    )

            now = utc_now()
            req.status = RequisitionStatus.CLOSED
            req.closed_at = now
            req.updated_at = now

            AuditService.log_audit(
                db=db,
                entity_type="JobRequisition",
                entity_id=requisition_id,
                action="CLOSE",
                actor=actor,
                new_state={
                    "status": req.status.value,
                    "closed_at": now.isoformat(),
                },
                reason="Requisition closed",
            )

            db.commit()
            db.refresh(req)
            return req

        except Exception:
            db.rollback()
            raise

    @classmethod
    def list_requisitions(
        cls,
        db: Session,
        department_id: Optional[int] = None,
        status: Optional[RequisitionStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[JobRequisition], int]:
        """List requisitions with filtering and pagination."""
        if department_id is not None and department_id <= 0:
            raise ValueError("Department ID must be positive.")
        if skip < 0:
            raise ValueError("Skip cannot be negative.")
        if limit < 1:
            raise ValueError("Limit must be at least 1.")

        query = db.query(JobRequisition)

        if department_id is not None:
            query = query.filter(
                JobRequisition.department_id == department_id
            )
        if status is not None:
            query = query.filter(JobRequisition.status == status)

        total = query.count()
        items = (
            query.order_by(JobRequisition.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        return items, total

    @classmethod
    def get_by_id(
        cls, db: Session, requisition_id: str
    ) -> Optional[JobRequisition]:
        """Retrieve a requisition by its ID."""
        return (
            db.query(JobRequisition)
            .filter(JobRequisition.requisition_id == requisition_id)
            .first()
        )
