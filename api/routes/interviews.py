
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy.orm import Session

from src.database import get_db
from src.models import RoundType, InterviewStatus, RecommendationEnum
from src.services.interview_service import InterviewService
from src.scheduling import InterviewerConflictError, SchedulingError
from src.workflow import WorkflowError

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/interviews",
    tags=["Interviews & Feedback"],
)


# -------------------- Request Schemas --------------------

class InterviewScheduleRequest(BaseModel):
    application_id: str = Field(..., min_length=1, max_length=100)
    round_number: int = Field(default=1, ge=1)
    round_type: RoundType
    scheduled_start: datetime
    scheduled_end: datetime
    interviewer_ids: List[str] = Field(..., min_length=1)

    @model_validator(mode="after")
    def validate_schedule(self):
        if self.scheduled_start >= self.scheduled_end:
            raise ValueError("scheduled_start must be before scheduled_end")

        if any(not interviewer_id.strip() for interviewer_id in self.interviewer_ids):
            raise ValueError("Interviewer IDs cannot be empty")

        if len(self.interviewer_ids) != len(set(self.interviewer_ids)):
            raise ValueError("Duplicate interviewer IDs are not allowed")

        return self


class FeedbackSubmitRequest(BaseModel):
    interviewer_id: str = Field(..., min_length=1, max_length=100)
    technical_rating: int = Field(..., ge=1, le=5)
    communication_rating: int = Field(..., ge=1, le=5)
    problem_solving_rating: int = Field(..., ge=1, le=5)
    recommendation: RecommendationEnum
    notes: str = Field(..., min_length=5, max_length=5000)

    @model_validator(mode="after")
    def validate_notes(self):
        if not self.notes.strip():
            raise ValueError("Feedback notes cannot be blank")
        return self


# -------------------- Response Schemas --------------------

class InterviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    interview_id: str
    application_id: str
    round_number: int
    round_type: str
    scheduled_start: datetime
    scheduled_end: datetime
    status: str
    created_at: datetime
    updated_at: datetime


class InterviewListResponse(BaseModel):
    total: int
    items: List[InterviewResponse]


class FeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    feedback_id: str
    interview_id: str
    interviewer_id: str
    technical_rating: int
    communication_rating: int
    problem_solving_rating: int
    overall_score: float
    recommendation: str
    notes: str
    version: int
    submitted_at: datetime
    updated_at: datetime


# -------------------- API Endpoints --------------------

@router.post(
    "",
    response_model=InterviewResponse,
    status_code=status.HTTP_201_CREATED,
)
def schedule_interview(
    req: InterviewScheduleRequest,
    db: Session = Depends(get_db),
):
    """Schedule an interview after checking availability and conflicts."""
    try:
        return InterviewService.schedule(
            db=db,
            application_id=req.application_id,
            round_number=req.round_number,
            round_type=req.round_type,
            scheduled_start=req.scheduled_start,
            scheduled_end=req.scheduled_end,
            interviewer_ids=req.interviewer_ids,
        )
    except InterviewerConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except SchedulingError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
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


@router.get("", response_model=InterviewListResponse)
def list_interviews(
    application_id: Optional[str] = Query(None, min_length=1),
    status_filter: Optional[InterviewStatus] = Query(
        None,
        alias="status",
        description="Filter by interview status",
    ),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List interviews with optional filters and pagination."""
    items, total = InterviewService.list_interviews(
        db=db,
        application_id=application_id,
        status=status_filter,
        skip=skip,
        limit=limit,
    )
    return {"total": total, "items": items}


@router.get("/{interview_id}", response_model=InterviewResponse)
def get_interview(
    interview_id: str,
    db: Session = Depends(get_db),
):
    """Retrieve an interview by ID."""
    interview = InterviewService.get_by_id(
        db=db,
        interview_id=interview_id,
    )

    if interview is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interview '{interview_id}' not found.",
        )

    return interview


@router.post(
    "/{interview_id}/feedback",
    response_model=FeedbackResponse,
)
def submit_interview_feedback(
    interview_id: str,
    req: FeedbackSubmitRequest,
    db: Session = Depends(get_db),
):
    """Submit structured interviewer feedback."""
    try:
        return InterviewService.submit_feedback(
            db=db,
            interview_id=interview_id,
            interviewer_id=req.interviewer_id,
            technical_rating=req.technical_rating,
            communication_rating=req.communication_rating,
            problem_solving_rating=req.problem_solving_rating,
            recommendation=req.recommendation,
            notes=req.notes,
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
