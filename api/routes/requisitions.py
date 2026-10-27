
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy.orm import Session

from src.database import get_db
from src.models import RequisitionStatus
from src.services.requisition_service import RequisitionService

router = APIRouter(
    prefix="/requisitions",
    tags=["Job Requisitions"],
)


# -------------------- Request Schemas --------------------

class RequisitionCreateRequest(BaseModel):
    title: str = Field(
        ...,
        min_length=2,
        max_length=150,
        examples=["Senior Backend Engineer"],
    )
    department_id: int = Field(..., gt=0, examples=[1])
    hiring_manager_id: str = Field(..., min_length=1, examples=["EMP-000001"])
    min_salary: float = Field(..., ge=0, examples=[110000.0])
    max_salary: float = Field(..., ge=0, examples=[150000.0])
    headcount: int = Field(default=1, ge=1, examples=[1])
    min_experience_years: float = Field(default=0.0, ge=0.0, examples=[3.0])
    currency: str = Field(default="USD", min_length=3, max_length=3)
    location: str = Field(default="Remote", min_length=1, max_length=150)
    required_skill_ids: Optional[List[int]] = None

    @model_validator(mode="after")
    def validate_salary_range(self):
        if self.min_salary > self.max_salary:
            raise ValueError("min_salary cannot exceed max_salary")
        if self.required_skill_ids is not None:
            if any(skill_id <= 0 for skill_id in self.required_skill_ids):
                raise ValueError("All skill IDs must be positive integers")
            if len(self.required_skill_ids) != len(set(self.required_skill_ids)):
                raise ValueError("Duplicate skill IDs are not allowed")
        return self


# -------------------- Response Schemas --------------------

class RequisitionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    requisition_id: str
    title: str
    department_id: int
    hiring_manager_id: str
    status: str
    headcount: int
    min_experience_years: float
    min_salary: float
    max_salary: float
    currency: str
    location: str
    opened_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class RequisitionListResponse(BaseModel):
    total: int
    items: List[RequisitionResponse]


# -------------------- API Endpoints --------------------

@router.post(
    "",
    response_model=RequisitionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_requisition(
    req: RequisitionCreateRequest,
    db: Session = Depends(get_db),
):
    """Create a job requisition in DRAFT status."""
    try:
        return RequisitionService.create_requisition(
            db=db,
            title=req.title,
            department_id=req.department_id,
            hiring_manager_id=req.hiring_manager_id,
            min_salary=req.min_salary,
            max_salary=req.max_salary,
            headcount=req.headcount,
            min_experience_years=req.min_experience_years,
            currency=req.currency,
            location=req.location,
            required_skill_ids=req.required_skill_ids,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get("", response_model=RequisitionListResponse)
def list_requisitions(
    department_id: Optional[int] = Query(None, gt=0),
    status_filter: Optional[RequisitionStatus] = Query(
        None,
        alias="status",
        description="Filter by requisition status",
    ),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List requisitions with optional filters and pagination."""
    items, total = RequisitionService.list_requisitions(
        db=db,
        department_id=department_id,
        status=status_filter,
        skip=skip,
        limit=limit,
    )
    return {"total": total, "items": items}


@router.get("/{requisition_id}", response_model=RequisitionResponse)
def get_requisition(
    requisition_id: str,
    db: Session = Depends(get_db),
):
    """Retrieve a requisition by ID."""
    requisition = RequisitionService.get_by_id(
        db=db,
        requisition_id=requisition_id,
    )

    if requisition is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Requisition '{requisition_id}' not found.",
        )

    return requisition


@router.post(
    "/{requisition_id}/open",
    response_model=RequisitionResponse,
)
def open_requisition(
    requisition_id: str,
    approver_id: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
):
    """Approve and open a requisition for sourcing."""
    try:
        return RequisitionService.open_requisition(
            db=db,
            requisition_id=requisition_id,
            approver_id=approver_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post(
    "/{requisition_id}/close",
    response_model=RequisitionResponse,
)
def close_requisition(
    requisition_id: str,
    actor: str = Query("HR_ADMIN", min_length=1),
    db: Session = Depends(get_db),
):
    """Close a requisition after checking candidate dispositions."""
    try:
        return RequisitionService.close_requisition(
            db=db,
            requisition_id=requisition_id,
            actor=actor,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
