
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from src.database import get_db
from src.models import Candidate


router = APIRouter(
    prefix="/candidates",
    tags=["Candidates"],
)


class CandidateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    candidate_id: str
    first_name: str
    last_name: str
    email: str
    phone: str
    location: str
    total_experience_years: float


class CandidateListResponse(BaseModel):
    total: int
    items: List[CandidateResponse]


@router.get("", response_model=CandidateListResponse)
def list_candidates(
    search: Optional[str] = Query(None, min_length=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Candidate)

    if search:
        term = f"%{search.strip()}%"
        query = query.filter(
            (Candidate.candidate_id.ilike(term))
            | (Candidate.first_name.ilike(term))
            | (Candidate.last_name.ilike(term))
            | (Candidate.email.ilike(term))
            | (Candidate.location.ilike(term))
        )

    total = query.count()
    items = (
        query.order_by(Candidate.candidate_id)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return {"total": total, "items": items}
