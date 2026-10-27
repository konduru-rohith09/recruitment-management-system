
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.orm import Session

from src.database import get_db
from src.models import OfferStatus, ApprovalStatus
from src.services.offer_service import OfferService
from src.offers import OfferPolicyError

router = APIRouter(
    prefix="/offers",
    tags=["Offers & Compensation"],
)


# -------------------- Request Schemas --------------------

class OfferCreateRequest(BaseModel):
    application_id: str = Field(..., min_length=1, max_length=100)
    base_salary: float = Field(..., gt=0)
    sign_on_bonus: float = Field(default=0.0, ge=0)
    equity_shares: int = Field(default=0, ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    approver_id: Optional[str] = Field(default=None, min_length=1, max_length=100)


class OfferApproveRequest(BaseModel):
    approver_id: str = Field(..., min_length=1, max_length=100)
    status: ApprovalStatus = Field(default=ApprovalStatus.APPROVED)
    comments: Optional[str] = Field(default=None, max_length=2000)


class OfferDecisionRequest(BaseModel):
    decision: str = Field(..., min_length=1)
    actor: str = Field(default="CANDIDATE", min_length=1, max_length=100)
    reason: Optional[str] = Field(default=None, max_length=2000)

    @field_validator("decision")
    @classmethod
    def validate_decision(cls, value: str) -> str:
        normalized = value.strip().upper()
        allowed = {"ACCEPTED", "REJECTED", "WITHDRAWN"}

        if normalized not in allowed:
            raise ValueError(
                "decision must be ACCEPTED, REJECTED, or WITHDRAWN"
            )

        return normalized


# -------------------- Response Schemas --------------------

class OfferResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    offer_id: str
    application_id: str
    base_salary: float
    sign_on_bonus: float
    equity_shares: int
    currency: str
    status: str
    is_out_of_band: bool
    exception_approved_by: Optional[str] = None
    issued_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    responded_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class OfferListResponse(BaseModel):
    total: int
    items: List[OfferResponse]


# -------------------- API Endpoints --------------------

@router.post(
    "",
    response_model=OfferResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_offer(
    req: OfferCreateRequest,
    db: Session = Depends(get_db),
):
    """Create an offer draft and validate compensation policies."""
    try:
        return OfferService.create_offer(
            db=db,
            application_id=req.application_id,
            base_salary=req.base_salary,
            sign_on_bonus=req.sign_on_bonus,
            equity_shares=req.equity_shares,
            currency=req.currency.upper(),
            approver_id=req.approver_id,
        )
    except OfferPolicyError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get("", response_model=OfferListResponse)
def list_offers(
    application_id: Optional[str] = Query(None, min_length=1),
    status_filter: Optional[OfferStatus] = Query(
        None,
        alias="status",
        description="Filter by offer status",
    ),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List offers with optional filters and pagination."""
    items, total = OfferService.list_offers(
        db=db,
        application_id=application_id,
        status=status_filter,
        skip=skip,
        limit=limit,
    )

    return {"total": total, "items": items}


@router.get("/{offer_id}", response_model=OfferResponse)
def get_offer(
    offer_id: str,
    db: Session = Depends(get_db),
):
    """Retrieve an offer by ID."""
    offer = OfferService.get_by_id(
        db=db,
        offer_id=offer_id,
    )

    if offer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Offer '{offer_id}' not found.",
        )

    return offer


@router.post("/{offer_id}/approve", response_model=OfferResponse)
def approve_offer(
    offer_id: str,
    req: OfferApproveRequest,
    db: Session = Depends(get_db),
):
    """Record an approval decision for an offer."""
    try:
        return OfferService.approve_offer(
            db=db,
            offer_id=offer_id,
            approver_id=req.approver_id,
            status=req.status,
            comments=req.comments,
        )
    except OfferPolicyError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post("/{offer_id}/issue", response_model=OfferResponse)
def issue_offer(
    offer_id: str,
    expiry_days: int = Query(7, ge=1, le=30),
    actor: str = Query("OFFER_COORDINATOR", min_length=1, max_length=100),
    db: Session = Depends(get_db),
):
    """Issue an approved offer to the candidate."""
    try:
        return OfferService.issue_offer(
            db=db,
            offer_id=offer_id,
            expiry_days=expiry_days,
            actor=actor,
        )
    except OfferPolicyError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post("/{offer_id}/decision", response_model=OfferResponse)
def record_candidate_decision(
    offer_id: str,
    req: OfferDecisionRequest,
    db: Session = Depends(get_db),
):
    """Record the candidate's response to an offer."""
    try:
        return OfferService.record_decision(
            db=db,
            offer_id=offer_id,
            decision=req.decision,
            actor=req.actor,
            reason=req.reason,
        )
    except OfferPolicyError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
