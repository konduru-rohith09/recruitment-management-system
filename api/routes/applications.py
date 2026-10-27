
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from src.database import get_db
from src.models import ApplicationStage
from src.services.application_service import ApplicationService
from src.workflow import WorkflowError
from src.screening import ScreeningError

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/applications",
    tags=["Candidate Applications"],
)


# -------------------- Request Schemas --------------------

class ApplicationCreateRequest(BaseModel):
    candidate_id: str = Field(..., min_length=1, max_length=100)
    requisition_id: str = Field(..., min_length=1, max_length=100)
    actor: str = Field(
        default="CANDIDATE_PORTAL",
        min_length=1,
        max_length=100,
    )


class ApplicationScreenRequest(BaseModel):
    assessment_score: float = Field(default=75.0, ge=0.0, le=100.0)
    actor: str = Field(
        default="RECRUITER_SCREENER",
        min_length=1,
        max_length=100,
    )


class StageTransitionRequest(BaseModel):
    target_stage: ApplicationStage
    actor: str = Field(default="RECRUITER", min_length=1, max_length=100)
    reason: str = Field(..., min_length=3, max_length=1000)


# -------------------- Response Schemas --------------------

class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    application_id: str
    candidate_id: str
    requisition_id: str
    current_stage: str
    applied_at: datetime
    updated_at: datetime
    screening_score: Optional[float] = None
    decision_reason: Optional[str] = None


class ApplicationListResponse(BaseModel):
    total: int
    items: List[ApplicationResponse]


class ScreeningResultResponse(BaseModel):
    application_id: str
    rule_version: str
    skill_match_score: float
    experience_score: float
    assessment_score: float
    final_score: float
    threshold: float
    decision: str
    reason_codes: List[str]
    evaluated_at: datetime


# -------------------- API Endpoints --------------------

@router.post(
    "",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_application(
    req: ApplicationCreateRequest,
    db: Session = Depends(get_db),
):
    """Submit a candidate application."""
    try:
        application, _ = ApplicationService.apply(
            db=db,
            candidate_id=req.candidate_id,
            requisition_id=req.requisition_id,
            actor=req.actor,
        )
        return application
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get("", response_model=ApplicationListResponse)
def list_applications(
    requisition_id: Optional[str] = Query(None, min_length=1),
    candidate_id: Optional[str] = Query(None, min_length=1),
    stage: Optional[ApplicationStage] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List applications with optional filters and pagination."""
    items, total = ApplicationService.list_applications(
        db=db,
        requisition_id=requisition_id,
        candidate_id=candidate_id,
        stage=stage,
        skip=skip,
        limit=limit,
    )
    return {"total": total, "items": items}


@router.get("/{application_id}", response_model=ApplicationResponse)
def get_application(
    application_id: str,
    db: Session = Depends(get_db),
):
    """Retrieve an application by ID."""
    application = ApplicationService.get_by_id(
        db=db,
        application_id=application_id,
    )

    if application is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application '{application_id}' not found.",
        )

    return application


@router.post("/{application_id}/screen", response_model=ScreeningResultResponse)
def screen_application(
    application_id: str,
    req: ApplicationScreenRequest,
    db: Session = Depends(get_db),
):
    """Evaluate an application against active screening rules."""
    try:
        result = ApplicationService.screen_application(
            db=db,
            application_id=application_id,
            assessment_score=req.assessment_score,
            actor=req.actor,
        )

        try:
            reason_codes = json.loads(result.reason_codes_json)
        except (TypeError, json.JSONDecodeError) as exc:
            logger.exception("Invalid reason_codes_json for application %s", application_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Invalid screening result data.",
            ) from exc

        return ScreeningResultResponse(
            application_id=result.application_id,
            rule_version=result.rule_version,
            skill_match_score=result.skill_match_score,
            experience_score=result.experience_score,
            assessment_score=result.assessment_score,
            final_score=result.final_score,
            threshold=result.threshold,
            decision=result.decision,
            reason_codes=reason_codes,
            evaluated_at=result.evaluated_at,
        )

    except ScreeningError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post("/{application_id}/transition", response_model=ApplicationResponse)
def transition_application_stage(
    application_id: str,
    req: StageTransitionRequest,
    db: Session = Depends(get_db),
):
    """Transition an application after validating workflow rules."""
    try:
        return ApplicationService.transition_stage(
            db=db,
            application_id=application_id,
            target_stage=req.target_stage,
            actor=req.actor,
            reason=req.reason,
        )
    except WorkflowError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
