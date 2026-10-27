
import logging
from datetime import timedelta
from typing import Optional

from sqlalchemy.orm import Session

from src.models import (
    Offer,
    JobRequisition,
    Application,
    OfferApproval,
    OfferStatus,
    ApplicationStage,
    RequisitionStatus,
    ApprovalStatus,
    utc_now,
)
from src.workflow import WorkflowEngine, WorkflowError

logger = logging.getLogger("recruitment_system.offers")


class OfferPolicyError(Exception):
    """Raised when offer operations violate compensation or approval policies."""


class OfferService:
    """Manage offer creation, approvals, issuance, and candidate decisions."""

    @classmethod
    def create_offer(
        cls,
        db: Session,
        offer_id: str,
        application_id: str,
        base_salary: float,
        sign_on_bonus: float = 0.0,
        equity_shares: int = 0,
        currency: str = "USD",
        approver_id: Optional[str] = None,
        allow_out_of_band_without_approval: bool = False,
    ) -> Offer:
        """Create a draft offer and validate its compensation band."""
        if not offer_id or not offer_id.strip():
            raise OfferPolicyError("Offer ID is required.")

        if not application_id or not application_id.strip():
            raise OfferPolicyError("Application ID is required.")

        if base_salary <= 0:
            raise OfferPolicyError("Base salary must be greater than zero.")

        if sign_on_bonus < 0:
            raise OfferPolicyError("Sign-on bonus cannot be negative.")

        if equity_shares < 0:
            raise OfferPolicyError("Equity shares cannot be negative.")

        if not currency or not currency.strip():
            raise OfferPolicyError("Currency is required.")

        existing_offer = (
            db.query(Offer)
            .filter(Offer.offer_id == offer_id)
            .first()
        )
        if existing_offer:
            raise OfferPolicyError(
                f"Offer '{offer_id}' already exists."
            )

        try:
            application = (
                db.query(Application)
                .filter(
                    Application.application_id == application_id
                )
                .first()
            )
            if application is None:
                raise OfferPolicyError(
                    f"Application '{application_id}' does not exist."
                )

            requisition = (
                db.query(JobRequisition)
                .filter(
                    JobRequisition.requisition_id
                    == application.requisition_id
                )
                .first()
            )
            if requisition is None:
                raise OfferPolicyError(
                    f"Requisition for application '{application_id}' "
                    "was not found."
                )

            if requisition.status != RequisitionStatus.OPEN:
                raise OfferPolicyError(
                    f"Cannot create an offer for application "
                    f"'{application_id}': requisition "
                    f"'{requisition.requisition_id}' is "
                    f"{requisition.status.value} (must be OPEN)."
                )

            if application.current_stage not in (
                ApplicationStage.DECISION_PENDING,
                ApplicationStage.OFFER_PENDING_APPROVAL,
            ):
                raise OfferPolicyError(
                    "An offer can only be created for an application "
                    "in DECISION_PENDING or OFFER_PENDING_APPROVAL."
                )

            is_out_of_band = (
                base_salary < requisition.min_salary
                or base_salary > requisition.max_salary
            )

            if (
                is_out_of_band
                and not allow_out_of_band_without_approval
                and not approver_id
            ):
                raise OfferPolicyError(
                    f"Proposed salary {currency.upper()} {base_salary:,.2f} "
                    f"exceeds requisition maximum "
                    f"{requisition.max_salary:,.2f}. "
                    "An executive exception approval is required."
)

            now = utc_now()
            normalized_currency = currency.strip().upper()

            offer = Offer(
                offer_id=offer_id.strip(),
                application_id=application_id.strip(),
                base_salary=base_salary,
                sign_on_bonus=sign_on_bonus,
                equity_shares=equity_shares,
                currency=normalized_currency,
                status=OfferStatus.DRAFT,
                is_out_of_band=is_out_of_band,
                # Exception approval is recorded only after an explicit APPROVED decision.
                exception_approved_by=None,
                created_at=now,
                updated_at=now,
            )
            db.add(offer)
            db.flush()

            approval = OfferApproval(
                offer_id=offer.offer_id,
                approver_id=(
                    approver_id.strip()
                    if approver_id and approver_id.strip()
                    else requisition.hiring_manager_id
                ),
                status=ApprovalStatus.PENDING,
                created_at=now,
            )
            db.add(approval)

            db.commit()
            db.refresh(offer)

            logger.info("Created offer %s", offer.offer_id)
            return offer

        except Exception:
            db.rollback()
            raise

    @classmethod
    def approve_offer(
        cls,
        db: Session,
        offer_id: str,
        approver_id: str,
        status: ApprovalStatus = ApprovalStatus.APPROVED,
        comments: Optional[str] = None,
    ) -> Offer:
        """Record an approval decision on a draft offer."""
        if not offer_id or not offer_id.strip():
            raise OfferPolicyError("Offer ID is required.")

        if not approver_id or not approver_id.strip():
            raise OfferPolicyError("Approver ID is required.")

        try:
            offer = (
                db.query(Offer)
                .filter(Offer.offer_id == offer_id)
                .first()
            )
            if offer is None:
                raise OfferPolicyError(
                    f"Offer '{offer_id}' not found."
                )

            if offer.status not in (
                OfferStatus.DRAFT,
                OfferStatus.PENDING_APPROVAL,
                OfferStatus.APPROVED,
            ):
                raise OfferPolicyError(
                    f"Cannot approve offer '{offer_id}' while its status "
                    f"is {offer.status.value}."
                )

            approval = (
                db.query(OfferApproval)
                .filter(
                    OfferApproval.offer_id == offer_id,
                    OfferApproval.approver_id == approver_id.strip(),
                )
                .first()
            )

            if approval is None:
                approval = OfferApproval(
                    offer_id=offer_id,
                    approver_id=approver_id.strip(),
                    created_at=utc_now(),
                )
                db.add(approval)

            approval.status = status
            approval.comments = comments.strip() if comments else None
            approval.decided_at = utc_now()

            if status == ApprovalStatus.APPROVED:
                offer.status = OfferStatus.APPROVED
                if offer.is_out_of_band:
                    offer.exception_approved_by = approver_id.strip()
            elif status == ApprovalStatus.REJECTED:
                offer.status = OfferStatus.REJECTED
                # A rejected approval must not leave a previous exception approval active.
                if offer.is_out_of_band:
                    offer.exception_approved_by = None
            elif status == ApprovalStatus.PENDING:
                offer.status = OfferStatus.PENDING_APPROVAL
                # Pending is not an authorization to issue an out-of-band offer.
                if offer.is_out_of_band:
                    offer.exception_approved_by = None

            offer.updated_at = utc_now()

            db.commit()
            db.refresh(offer)

            logger.info(
                "Offer %s approval recorded: %s",
                offer_id,
                status.value if hasattr(status, "value") else status,
            )
            return offer

        except Exception:
            db.rollback()
            raise

    @classmethod
    def issue_offer(
        cls,
        db: Session,
        offer_id: str,
        expiry_days: int = 7,
        actor: str = "OFFER_COORDINATOR",
        bypass_approval_check: bool = False,
    ) -> Offer:
        """Issue an offer and transition its application to OFFERED."""
        if not 1 <= expiry_days <= 30:
            raise OfferPolicyError(
                "Offer expiry must be between 1 and 30 days."
            )

        if not actor or not actor.strip():
            raise OfferPolicyError("Actor is required.")

        try:
            offer = (
                db.query(Offer)
                .filter(Offer.offer_id == offer_id)
                .first()
            )
            if offer is None:
                raise OfferPolicyError(
                    f"Offer '{offer_id}' not found."
                )

            application = (
                db.query(Application)
                .filter(
                    Application.application_id == offer.application_id
                )
                .first()
            )
            if application is None:
                raise OfferPolicyError(
                    f"Application '{offer.application_id}' not found."
                )

            requisition = (
                db.query(JobRequisition)
                .filter(
                    JobRequisition.requisition_id
                    == application.requisition_id
                )
                .first()
            )
            if requisition is None:
                raise OfferPolicyError(
                    f"Requisition '{application.requisition_id}' not found."
                )

            if requisition.status != RequisitionStatus.OPEN:
                raise OfferPolicyError(
                    f"Cannot issue offer: requisition "
                    f"'{requisition.requisition_id}' is "
                    f"{requisition.status.value} (must be OPEN)."
                )

            if not bypass_approval_check:
                if offer.status != OfferStatus.APPROVED:
                    raise OfferPolicyError(
                        f"Cannot issue offer '{offer_id}': status is "
                        f"{offer.status.value} (must be APPROVED)."
                    )

                if (
                    offer.is_out_of_band
                    and not offer.exception_approved_by
                ):
                    raise OfferPolicyError(
                        f"Cannot issue offer '{offer_id}': "
                        "out-of-band compensation lacks executive approval."
                    )

            now = utc_now()
            offer.status = OfferStatus.ISSUED
            offer.issued_at = now
            offer.expires_at = now + timedelta(days=expiry_days)
            offer.updated_at = now

            WorkflowEngine.transition_stage(
                db=db,
                application_id=application.application_id,
                target_stage=ApplicationStage.OFFERED,
                actor=actor.strip(),
                reason=(
                    f"Offer {offer.offer_id} issued with base salary "
                    f"{offer.currency} {offer.base_salary:,.2f}"
                ),
            )

            db.commit()
            db.refresh(offer)

            logger.info("Issued offer %s", offer_id)
            return offer

        except WorkflowError as exc:
            db.rollback()
            raise OfferPolicyError(str(exc)) from exc
        except Exception:
            db.rollback()
            raise

    @classmethod
    def record_candidate_decision(
        cls,
        db: Session,
        offer_id: str,
        decision: str,
        actor: str = "CANDIDATE",
        reason: Optional[str] = None,
    ) -> Offer:
        """Record a candidate decision and update the application lifecycle."""
        if not decision or decision.strip().upper() not in {
            "ACCEPTED",
            "REJECTED",
            "WITHDRAWN",
        }:
            raise OfferPolicyError(
                "Invalid decision. Expected ACCEPTED, REJECTED, or WITHDRAWN."
            )

        if not actor or not actor.strip():
            raise OfferPolicyError("Actor is required.")

        decision = decision.strip().upper()

        try:
            offer = (
                db.query(Offer)
                .filter(Offer.offer_id == offer_id)
                .first()
            )
            if offer is None:
                raise OfferPolicyError(
                    f"Offer '{offer_id}' not found."
                )

            if offer.status != OfferStatus.ISSUED:
                raise OfferPolicyError(
                    f"Cannot record decision: offer '{offer_id}' is not "
                    f"ISSUED (current status: {offer.status.value})."
                )

            now = utc_now()

            if offer.expires_at:
                expiry = offer.expires_at
                if expiry.tzinfo is not None:
                    expiry = expiry.replace(tzinfo=None)

                if now > expiry:
                    offer.status = OfferStatus.EXPIRED
                    offer.updated_at = now

                    # Only transition the application when its current stage
                    # permits OFFER_EXPIRED. An expired offer can be marked
                    # EXPIRED even if the application is already in another
                    # stage (for example SCREENING).
                    application_for_expiry = (
                        db.query(Application)
                        .filter(
                            Application.application_id == offer.application_id
                        )
                        .first()
                    )

                    if (
                        application_for_expiry is not None
                        and application_for_expiry.current_stage
                        == ApplicationStage.OFFERED
                    ):
                        WorkflowEngine.transition_stage(
                            db=db,
                            application_id=offer.application_id,
                            target_stage=ApplicationStage.OFFER_EXPIRED,
                            actor="SYSTEM",
                            reason="Offer expired past deadline",
                        )

                    # Preserve the expired offer status even when the
                    # application stage cannot transition to OFFER_EXPIRED.
                    db.commit()

                    raise OfferPolicyError(
                        f"Offer '{offer_id}' expired on "
                        f"{offer.expires_at.isoformat()}."
                    )

            application = (
                db.query(Application)
                .filter(
                    Application.application_id == offer.application_id
                )
                .first()
            )
            if application is None:
                raise OfferPolicyError(
                    f"Application '{offer.application_id}' not found."
                )

            requisition = (
                db.query(JobRequisition)
                .filter(
                    JobRequisition.requisition_id
                    == application.requisition_id
                )
                .first()
            )
            if requisition is None:
                raise OfferPolicyError(
                    f"Requisition '{application.requisition_id}' not found."
                )

            target_stages = {
                "ACCEPTED": ApplicationStage.ACCEPTED,
                "REJECTED": ApplicationStage.OFFER_REJECTED,
                "WITHDRAWN": ApplicationStage.WITHDRAWN,
            }

            WorkflowEngine.transition_stage(
                db=db,
                application_id=application.application_id,
                target_stage=target_stages[decision],
                actor=actor.strip(),
                reason=(
                    reason.strip()
                    if reason and reason.strip()
                    else f"Candidate {decision.lower()} offer"
                ),
            )

            status_mapping = {
                "ACCEPTED": OfferStatus.ACCEPTED,
                "REJECTED": OfferStatus.REJECTED,
                "WITHDRAWN": OfferStatus.WITHDRAWN,
            }
            offer.status = status_mapping[decision]
            offer.responded_at = now
            offer.updated_at = now

            if decision == "ACCEPTED":
                accepted_count = (
                    db.query(Application)
                    .filter(
                        Application.requisition_id
                        == requisition.requisition_id,
                        Application.current_stage
                        == ApplicationStage.ACCEPTED,
                    )
                    .count()
                )

                if accepted_count >= requisition.headcount:
                    requisition.status = RequisitionStatus.FILLED
                    requisition.closed_at = now
                    requisition.updated_at = now

            db.commit()
            db.refresh(offer)

            logger.info(
                "Recorded decision %s for offer %s",
                decision,
                offer_id,
            )
            return offer

        except WorkflowError as exc:
            db.rollback()
            raise OfferPolicyError(str(exc)) from exc
        except OfferPolicyError:
            # Preserve the committed EXPIRED state when expiration was detected.
            raise
        except Exception:
            db.rollback()
            raise
