
import logging
from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import desc
from sqlalchemy.orm import Session

from src.models import (
    Interview,
    Feedback,
    InterviewStatus,
    RoundType,
    RecommendationEnum,
)
from src.scheduling import SchedulingService
from src.workflow import WorkflowEngine

logger = logging.getLogger("recruitment_system.interview_service")


class InterviewService:
    """Manage interview scheduling, assignments, and scorecard feedback."""

    @classmethod
    def generate_next_interview_id(
        cls, db: Session, year: int = 2026
    ) -> str:
        """Generate the next interview ID in INT-YYYY-NNNNNN format."""
        prefix = f"INT-{year}-"

        last_interview = (
            db.query(Interview)
            .filter(Interview.interview_id.like(f"{prefix}%"))
            .order_by(desc(Interview.interview_id))
            .first()
        )

        if last_interview:
            try:
                sequence = int(
                    last_interview.interview_id.rsplit("-", 1)[-1]
                ) + 1
            except (ValueError, AttributeError):
                logger.warning(
                    "Could not parse the last interview ID: %s",
                    last_interview.interview_id,
                )
                sequence = 1
        else:
            sequence = 1

        return f"{prefix}{sequence:06d}"

    @classmethod
    def schedule(
        cls,
        db: Session,
        application_id: str,
        round_number: int,
        round_type: RoundType,
        scheduled_start: datetime,
        scheduled_end: datetime,
        interviewer_ids: List[str],
        custom_id: Optional[str] = None,
        allow_conflict_injection: bool = False,
    ) -> Interview:
        """Schedule an interview through the scheduling service."""
        if not application_id or not application_id.strip():
            raise ValueError("Application ID is required.")

        if round_number < 1:
            raise ValueError("Round number must be at least 1.")

        if scheduled_start >= scheduled_end:
            raise ValueError(
                "Interview start time must be earlier than end time."
            )

        if not interviewer_ids:
            raise ValueError(
                "At least one interviewer must be assigned."
            )

        normalized_ids = [
            interviewer_id.strip()
            for interviewer_id in interviewer_ids
            if interviewer_id and interviewer_id.strip()
        ]

        if len(normalized_ids) != len(interviewer_ids):
            raise ValueError(
                "Interviewer IDs cannot be empty."
            )

        if len(normalized_ids) != len(set(normalized_ids)):
            raise ValueError(
                "Duplicate interviewer IDs are not allowed."
            )

        interview_id = (
            custom_id.strip()
            if custom_id and custom_id.strip()
            else cls.generate_next_interview_id(db)
        )

        existing_interview = (
            db.query(Interview)
            .filter(Interview.interview_id == interview_id)
            .first()
        )
        if existing_interview:
            raise ValueError(
                f"Interview ID '{interview_id}' already exists."
            )

        logger.info(
            "Scheduling interview %s for application %s",
            interview_id,
            application_id,
        )

        return SchedulingService.schedule_interview(
            db=db,
            interview_id=interview_id,
            application_id=application_id,
            round_number=round_number,
            round_type=round_type,
            scheduled_start=scheduled_start,
            scheduled_end=scheduled_end,
            interviewer_ids=normalized_ids,
            allow_conflict_injection=allow_conflict_injection,
        )

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
        """Submit validated interviewer scorecard feedback."""
        if not interview_id or not interview_id.strip():
            raise ValueError("Interview ID is required.")

        if not interviewer_id or not interviewer_id.strip():
            raise ValueError("Interviewer ID is required.")

        ratings = {
            "technical_rating": technical_rating,
            "communication_rating": communication_rating,
            "problem_solving_rating": problem_solving_rating,
        }

        for rating_name, rating_value in ratings.items():
            if not 1 <= rating_value <= 5:
                raise ValueError(
                    f"{rating_name} must be between 1 and 5."
                )

        if not notes or not notes.strip():
            raise ValueError("Feedback notes are required.")

        return WorkflowEngine.submit_feedback(
            db=db,
            interview_id=interview_id,
            interviewer_id=interviewer_id,
            technical_rating=technical_rating,
            communication_rating=communication_rating,
            problem_solving_rating=problem_solving_rating,
            recommendation=recommendation,
            notes=notes.strip(),
        )

    @classmethod
    def list_interviews(
        cls,
        db: Session,
        application_id: Optional[str] = None,
        status: Optional[InterviewStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[Interview], int]:
        """List interviews with optional filters and pagination."""
        if skip < 0:
            raise ValueError("Skip cannot be negative.")

        if limit < 1:
            raise ValueError("Limit must be at least 1.")

        query = db.query(Interview)

        if application_id is not None:
            query = query.filter(
                Interview.application_id == application_id
            )

        if status is not None:
            query = query.filter(Interview.status == status)

        total = query.count()

        items = (
            query.order_by(Interview.scheduled_start.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        return items, total

    @classmethod
    def get_by_id(
        cls, db: Session, interview_id: str
    ) -> Optional[Interview]:
        """Retrieve an interview by its ID."""
        if not interview_id or not interview_id.strip():
            return None

        return (
            db.query(Interview)
            .filter(Interview.interview_id == interview_id)
            .first()
        )
