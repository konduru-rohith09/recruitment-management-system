
import logging
from typing import List, Optional, Tuple

from sqlalchemy import desc
from sqlalchemy.orm import Session

from src.models import Offer, OfferStatus, ApprovalStatus
from src.offers import OfferService as CoreOfferService

logger = logging.getLogger("recruitment_system.offer_service")


class OfferService:
    """Service facade for offer lifecycle management."""

    @classmethod
    def generate_next_offer_id(
        cls, db: Session, year: int = 2026
    ) -> str:
        """Generate the next ID in OFF-YYYY-NNNNNN format."""
        prefix = f"OFF-{year}-"

        last_offer = (
            db.query(Offer)
            .filter(Offer.offer_id.like(f"{prefix}%"))
            .order_by(desc(Offer.offer_id))
            .first()
        )

        if last_offer:
            try:
                sequence = int(
                    last_offer.offer_id.rsplit("-", 1)[-1]
                ) + 1
            except (ValueError, AttributeError):
                logger.warning(
                    "Could not parse the last offer ID: %s",
                    last_offer.offer_id,
                )
                sequence = 1
        else:
            sequence = 1

        return f"{prefix}{sequence:06d}"

    @classmethod
    def create_offer(
        cls,
        db: Session,
        application_id: str,
        base_salary: float,
        sign_on_bonus: float = 0.0,
        equity_shares: int = 0,
        currency: str = "USD",
        approver_id: Optional[str] = None,
        custom_id: Optional[str] = None,
        allow_out_of_band_without_approval: bool = False,
    ) -> Offer:
        """Create an offer through the core offer policy service."""
        if not application_id or not application_id.strip():
            raise ValueError("Application ID is required.")

        if base_salary <= 0:
            raise ValueError("Base salary must be greater than zero.")

        if sign_on_bonus < 0:
            raise ValueError("Sign-on bonus cannot be negative.")

        if equity_shares < 0:
            raise ValueError("Equity shares cannot be negative.")

        if not currency or not currency.strip():
            raise ValueError("Currency is required.")

        offer_id = (
            custom_id.strip()
            if custom_id and custom_id.strip()
            else cls.generate_next_offer_id(db)
        )

        existing_offer = (
            db.query(Offer)
            .filter(Offer.offer_id == offer_id)
            .first()
        )
        if existing_offer:
            raise ValueError(f"Offer ID '{offer_id}' already exists.")

        logger.info(
            "Creating offer %s for application %s",
            offer_id,
            application_id,
        )

        return CoreOfferService.create_offer(
            db=db,
            offer_id=offer_id,
            application_id=application_id,
            base_salary=base_salary,
            sign_on_bonus=sign_on_bonus,
            equity_shares=equity_shares,
            currency=currency.strip().upper(),
            approver_id=approver_id.strip() if approver_id else None,
            allow_out_of_band_without_approval=(
                allow_out_of_band_without_approval
            ),
        )

    @classmethod
    def approve_offer(
        cls,
        db: Session,
        offer_id: str,
        approver_id: str,
        status: ApprovalStatus = ApprovalStatus.APPROVED,
        comments: Optional[str] = None,
    ) -> Offer:
        """Record an approval decision through the core service."""
        if not offer_id or not offer_id.strip():
            raise ValueError("Offer ID is required.")

        if not approver_id or not approver_id.strip():
            raise ValueError("Approver ID is required.")

        return CoreOfferService.approve_offer(
            db=db,
            offer_id=offer_id,
            approver_id=approver_id.strip(),
            status=status,
            comments=comments.strip() if comments else None,
        )

    @classmethod
    def issue_offer(
        cls,
        db: Session,
        offer_id: str,
        expiry_days: int = 7,
        actor: str = "OFFER_COORDINATOR",
        bypass_approval_check: bool = False,
    ) -> Offer:
        """Issue an approved offer to the candidate."""
        if not offer_id or not offer_id.strip():
            raise ValueError("Offer ID is required.")

        if not 1 <= expiry_days <= 30:
            raise ValueError("Expiry days must be between 1 and 30.")

        if not actor or not actor.strip():
            raise ValueError("Actor is required.")

        return CoreOfferService.issue_offer(
            db=db,
            offer_id=offer_id,
            expiry_days=expiry_days,
            actor=actor.strip(),
            bypass_approval_check=bypass_approval_check,
        )

    @classmethod
    def record_decision(
        cls,
        db: Session,
        offer_id: str,
        decision: str,
        actor: str = "CANDIDATE",
        reason: Optional[str] = None,
    ) -> Offer:
        """Record the candidate's decision on an offer."""
        if not offer_id or not offer_id.strip():
            raise ValueError("Offer ID is required.")

        if not decision or not decision.strip():
            raise ValueError("Offer decision is required.")

        if not actor or not actor.strip():
            raise ValueError("Actor is required.")

        normalized_decision = decision.strip().upper()
        allowed_decisions = {"ACCEPTED", "REJECTED", "WITHDRAWN"}

        if normalized_decision not in allowed_decisions:
            raise ValueError(
                "Decision must be ACCEPTED, REJECTED, or WITHDRAWN."
            )

        return CoreOfferService.record_candidate_decision(
            db=db,
            offer_id=offer_id,
            decision=normalized_decision,
            actor=actor.strip(),
            reason=reason.strip() if reason else None,
        )

    @classmethod
    def list_offers(
        cls,
        db: Session,
        application_id: Optional[str] = None,
        status: Optional[OfferStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[Offer], int]:
        """List offers with optional filters and pagination."""
        if skip < 0:
            raise ValueError("Skip cannot be negative.")

        if limit < 1:
            raise ValueError("Limit must be at least 1.")

        query = db.query(Offer)

        if application_id is not None:
            query = query.filter(
                Offer.application_id == application_id
            )

        if status is not None:
            query = query.filter(Offer.status == status)

        total = query.count()

        items = (
            query.order_by(Offer.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        return items, total

    @classmethod
    def get_by_id(
        cls, db: Session, offer_id: str
    ) -> Optional[Offer]:
        """Retrieve an offer by its ID."""
        if not offer_id or not offer_id.strip():
            return None

        return (
            db.query(Offer)
            .filter(Offer.offer_id == offer_id)
            .first()
        )
