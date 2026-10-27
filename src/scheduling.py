
import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from src.models import (
    Interview,
    Interviewer,
    InterviewerAssignment,
    Application,
    InterviewStatus,
    RoundType,
    utc_now,
)

logger = logging.getLogger("recruitment_system.scheduling")


class SchedulingError(Exception):
    """Base exception for scheduling failures."""


class InterviewerConflictError(SchedulingError):
    """Raised when an interviewer is inactive or has a conflicting booking."""


class SchedulingService:
    """Manage interview scheduling, availability, and conflict resolution."""

    ACTIVE_CONFLICT_STATUSES = (
        InterviewStatus.SCHEDULED,
        InterviewStatus.RESCHEDULED,
        InterviewStatus.COMPLETED,
    )

    @classmethod
    def check_interviewer_availability(
        cls,
        db: Session,
        interviewer_id: str,
        start_time: datetime,
        end_time: datetime,
        exclude_interview_id: Optional[str] = None,
    ) -> bool:
        """Check interviewer activity and overlapping interview bookings."""
        if not interviewer_id or not interviewer_id.strip():
            raise InterviewerConflictError("Interviewer ID is required.")

        if start_time >= end_time:
            raise SchedulingError(
                "Interview start time must be earlier than end time."
            )

        interviewer = (
            db.query(Interviewer)
            .filter(Interviewer.interviewer_id == interviewer_id)
            .first()
        )

        if interviewer is None:
            raise InterviewerConflictError(
                f"Interviewer '{interviewer_id}' does not exist."
            )

        if not interviewer.is_active:
            raise InterviewerConflictError(
                f"Interviewer '{interviewer_id}' ({interviewer.name}) "
                "is currently inactive and cannot be scheduled."
    )

        conflict_query = (
            db.query(Interview)
            .join(
                InterviewerAssignment,
                Interview.interview_id
                == InterviewerAssignment.interview_id,
            )
            .filter(
                InterviewerAssignment.interviewer_id == interviewer_id,
                Interview.status.in_(cls.ACTIVE_CONFLICT_STATUSES),
                Interview.scheduled_start < end_time,
                Interview.scheduled_end > start_time,
            )
        )

        if exclude_interview_id:
            conflict_query = conflict_query.filter(
                Interview.interview_id != exclude_interview_id
            )

        conflict = conflict_query.first()

        if conflict:
            raise InterviewerConflictError(
                f"Conflict detected for interviewer '{interviewer_id}' "
                f"({interviewer.name}): already booked for interview "
                f"{conflict.interview_id} from "
                f"{conflict.scheduled_start.isoformat()} to "
                f"{conflict.scheduled_end.isoformat()}."
            )

        return True

    @classmethod
    def schedule_interview(
        cls,
        db: Session,
        interview_id: str,
        application_id: str,
        round_number: int,
        round_type: RoundType,
        scheduled_start: datetime,
        scheduled_end: datetime,
        interviewer_ids: List[str],
        allow_conflict_injection: bool = False,
    ) -> Interview:
        """Schedule an interview and assign interviewers atomically."""
        if not interview_id or not interview_id.strip():
            raise SchedulingError("Interview ID is required.")

        if not application_id or not application_id.strip():
            raise SchedulingError("Application ID is required.")

        if round_number < 1:
            raise SchedulingError("Round number must be at least 1.")

        if scheduled_start >= scheduled_end:
            raise SchedulingError(
                "Interview end time must be strictly after start time."
            )

        if not interviewer_ids:
            raise SchedulingError(
                "At least one interviewer must be assigned."
            )

        normalized_ids = [
            interviewer_id.strip()
            for interviewer_id in interviewer_ids
            if interviewer_id and interviewer_id.strip()
        ]

        if len(normalized_ids) != len(interviewer_ids):
            raise SchedulingError(
                "Interviewer IDs cannot be empty."
            )

        if len(normalized_ids) != len(set(normalized_ids)):
            raise SchedulingError(
                "Duplicate interviewer IDs are not allowed."
            )

        application = (
            db.query(Application)
            .filter(Application.application_id == application_id)
            .first()
        )

        if application is None:
            raise SchedulingError(
                f"Application '{application_id}' does not exist."
            )

        existing_interview = (
            db.query(Interview)
            .filter(Interview.interview_id == interview_id)
            .first()
        )

        if existing_interview is not None:
            raise SchedulingError(
                f"Interview '{interview_id}' already exists."
            )

        # Check every interviewer before creating any records.
        # Conflict injection is reserved for controlled anomaly testing.
        if not allow_conflict_injection:
            for interviewer_id in normalized_ids:
                cls.check_interviewer_availability(
                    db=db,
                    interviewer_id=interviewer_id,
                    start_time=scheduled_start,
                    end_time=scheduled_end,
                )

        try:
            now = utc_now()

            interview = Interview(
                interview_id=interview_id,
                application_id=application_id,
                round_number=round_number,
                round_type=round_type,
                scheduled_start=scheduled_start,
                scheduled_end=scheduled_end,
                status=InterviewStatus.SCHEDULED,
                created_at=now,
                updated_at=now,
            )

            db.add(interview)
            db.flush()

            assignments = [
                InterviewerAssignment(
                    interview_id=interview.interview_id,
                    interviewer_id=interviewer_id,
                    assigned_at=now,
                )
                for interviewer_id in normalized_ids
            ]

            db.add_all(assignments)
            db.commit()
            db.refresh(interview)

            logger.info(
                "Scheduled interview %s for application %s",
                interview_id,
                application_id,
            )

            return interview

        except Exception:
            db.rollback()
            logger.exception(
                "Failed to schedule interview %s",
                interview_id,
            )
            raise

    @classmethod
    def reschedule_interview(
        cls,
        db: Session,
        interview_id: str,
        new_start: datetime,
        new_end: datetime,
    ) -> Interview:
        """Reschedule an interview after checking interviewer availability."""
        if new_start >= new_end:
            raise SchedulingError(
                "Rescheduled end time must be after start time."
            )

        interview = (
            db.query(Interview)
            .filter(Interview.interview_id == interview_id)
            .first()
        )

        if interview is None:
            raise SchedulingError(
                f"Interview '{interview_id}' not found."
            )

        if interview.status == InterviewStatus.CANCELLED:
            raise SchedulingError(
                "A cancelled interview cannot be rescheduled."
            )

        assigned_ids = [
            assignment.interviewer_id
            for assignment in interview.assignments
        ]

        for interviewer_id in assigned_ids:
            cls.check_interviewer_availability(
                db=db,
                interviewer_id=interviewer_id,
                start_time=new_start,
                end_time=new_end,
                exclude_interview_id=interview_id,
            )

        try:
            interview.scheduled_start = new_start
            interview.scheduled_end = new_end
            interview.status = InterviewStatus.RESCHEDULED
            interview.updated_at = utc_now()

            db.commit()
            db.refresh(interview)

            logger.info("Rescheduled interview %s", interview_id)
            return interview

        except Exception:
            db.rollback()
            logger.exception(
                "Failed to reschedule interview %s",
                interview_id,
            )
            raise

    @classmethod
    def cancel_interview(
        cls,
        db: Session,
        interview_id: str,
        reason: str = "Cancelled by user",
    ) -> Interview:
        """Cancel an interview."""
        interview = (
            db.query(Interview)
            .filter(Interview.interview_id == interview_id)
            .first()
        )

        if interview is None:
            raise SchedulingError(
                f"Interview '{interview_id}' not found."
            )

        if interview.status == InterviewStatus.CANCELLED:
            raise SchedulingError(
                f"Interview '{interview_id}' is already cancelled."
            )

        try:
            interview.status = InterviewStatus.CANCELLED
            interview.updated_at = utc_now()

            db.commit()
            db.refresh(interview)

            logger.info(
                "Cancelled interview %s. Reason: %s",
                interview_id,
                reason,
            )
            return interview

        except Exception:
            db.rollback()
            logger.exception(
                "Failed to cancel interview %s",
                interview_id,
            )
            raise
