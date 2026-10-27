
import json
import logging
import math
from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from src.models import (
    Application,
    JobRequisition,
    Candidate,
    ScreeningRule,
    CandidateScreeningResult,
    CandidateSkill,
    RequisitionRequiredSkill,
    ApplicationStage,
    ApplicationEvent,
    utc_now,
)

logger = logging.getLogger("recruitment_system.screening")


class ScreeningError(Exception):
    """Raised when application screening or validation fails."""


class ScreeningEngine:
    """Configurable, explainable screening based on job-related criteria."""

    @staticmethod
    def validate_rule_weights(rule: ScreeningRule) -> None:
        """Validate weights, their sum, and the passing threshold."""
        weights = (
            rule.skill_weight,
            rule.experience_weight,
            rule.assessment_weight,
        )

        if any(
            weight is None or not math.isfinite(float(weight))
            for weight in weights
        ):
            raise ScreeningError(
                "Screening rule weights must be finite numbers."
            )

        if any(float(weight) < 0 for weight in weights):
            raise ScreeningError(
                "Screening rule weights cannot be negative."
            )

        total = sum(float(weight) for weight in weights)

        if abs(total - 1.0) > 0.001:
            raise ScreeningError(
                f"Screening rule weights must sum to 1.0. "
                f"Current sum: {total:.4f}"
            )

        threshold = rule.passing_threshold

        if (
            threshold is None
            or not math.isfinite(float(threshold))
            or not 0 <= float(threshold) <= 100
        ):
            raise ScreeningError(
                "Screening passing threshold must be between 0 and 100."
            )

    @classmethod
    def calculate_skills_score(
        cls,
        candidate_skills: List[CandidateSkill],
        required_skills: List[RequisitionRequiredSkill],
    ) -> Tuple[float, List[str]]:
        """Calculate skill match score from 0 to 100."""
        if not required_skills:
            return 100.0, ["NO_REQUIRED_SKILLS_SPECIFIED"]

        candidate_skill_map = {
            skill.skill_id: skill for skill in candidate_skills
        }

        matched_weight = 0.0
        reasons: List[str] = []

        for requirement in required_skills:
            candidate_skill = candidate_skill_map.get(
                requirement.skill_id
            )

            if candidate_skill is None:
                reasons.append(
                    f"MISSING_SKILL_ID_{requirement.skill_id}"
                )
                continue

            proficiency = candidate_skill.proficiency_level
            years_experience = candidate_skill.years_experience
            minimum_experience = requirement.min_experience_years

            if (
                proficiency is None
                or not math.isfinite(float(proficiency))
                or not 1 <= float(proficiency) <= 5
            ):
                raise ScreeningError(
                    f"Invalid proficiency for skill "
                    f"{requirement.skill_id}; expected a value from 1 to 5."
                )

            if (
                years_experience is None
                or not math.isfinite(float(years_experience))
                or float(years_experience) < 0
            ):
                raise ScreeningError(
                    f"Invalid years of experience for skill "
                    f"{requirement.skill_id}."
                )

            if (
                minimum_experience is None
                or not math.isfinite(float(minimum_experience))
                or float(minimum_experience) < 0
            ):
                raise ScreeningError(
                    f"Invalid minimum experience for skill "
                    f"{requirement.skill_id}."
                )

            proficiency_factor = float(proficiency) / 5.0

            experience_factor = (
                1.0
                if float(minimum_experience) == 0
                else min(
                    1.0,
                    float(years_experience)
                    / float(minimum_experience),
                )
            )

            matched_weight += (
                proficiency_factor * 0.7
                + experience_factor * 0.3
            )

        score = matched_weight / len(required_skills) * 100.0

        return round(min(100.0, max(0.0, score)), 2), reasons

    @classmethod
    def calculate_experience_score(
        cls,
        candidate_years: float,
        req_min_years: float,
    ) -> Tuple[float, List[str]]:
        """Calculate experience score from 0 to 100."""
        if (
            candidate_years is None
            or not math.isfinite(float(candidate_years))
            or float(candidate_years) < 0
        ):
            raise ScreeningError(
                "Candidate experience must be a finite, non-negative value."
            )

        if (
            req_min_years is None
            or not math.isfinite(float(req_min_years))
            or float(req_min_years) < 0
        ):
            raise ScreeningError(
                "Required experience must be a finite, non-negative value."
            )

        candidate_years = float(candidate_years)
        req_min_years = float(req_min_years)

        if req_min_years == 0:
            return 100.0, ["NO_EXPERIENCE_REQUIREMENT"]

        if candidate_years >= req_min_years:
            score = min(
                100.0,
                80.0 + (candidate_years - req_min_years) * 5.0,
            )
            reasons = ["MEETS_OR_EXCEEDS_EXPERIENCE"]
        else:
            score = (candidate_years / req_min_years) * 75.0
            reasons = [
                f"BELOW_MIN_EXPERIENCE_REQ_{req_min_years:g}Y"
            ]

        return round(max(0.0, min(100.0, score)), 2), reasons

    @classmethod
    def evaluate_application(
        cls,
        db: Session,
        application_id: str,
        assessment_score: float = 75.0,
        actor: str = "SYSTEM_SCREENER",
        evaluated_at: Optional[datetime] = None,
    ) -> CandidateScreeningResult:
        """Evaluate an application and persist its screening result."""
        if (
            not isinstance(application_id, str)
            or not application_id.strip()
        ):
            raise ScreeningError("Application ID must not be empty.")

        if (
            isinstance(assessment_score, bool)
            or not isinstance(assessment_score, (int, float))
            or not math.isfinite(float(assessment_score))
            or not 0 <= float(assessment_score) <= 100
        ):
            raise ScreeningError(
                "Assessment score must be a finite number between 0 and 100."
            )

        if not isinstance(actor, str) or not actor.strip():
            raise ScreeningError("Screening actor must not be empty.")

        if evaluated_at is not None and not isinstance(
            evaluated_at, datetime
        ):
            raise ScreeningError(
                "Evaluation timestamp must be a datetime."
            )

        eval_time = evaluated_at or utc_now()

        try:
            application = (
                db.query(Application)
                .filter(
                    Application.application_id == application_id.strip()
                )
                .with_for_update()
                .first()
            )

            if application is None:
                raise ScreeningError(
                    f"Application {application_id} not found."
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
                raise ScreeningError(
                    f"Requisition for application "
                    f"{application.application_id} was not found."
                )

            candidate = (
                db.query(Candidate)
                .filter(
                    Candidate.candidate_id == application.candidate_id
                )
                .first()
            )

            if candidate is None:
                raise ScreeningError(
                    f"Candidate for application "
                    f"{application.application_id} was not found."
                )

            rule = (
                db.query(ScreeningRule)
                .filter(
                    ScreeningRule.requisition_id
                    == requisition.requisition_id,
                    ScreeningRule.is_active.is_(True),
                )
                .order_by(ScreeningRule.rule_version.desc())
                .first()
            )

            if rule is None:
                rule = ScreeningRule(
                    requisition_id=requisition.requisition_id,
                    rule_version="1.0-default",
                    skill_weight=0.60,
                    experience_weight=0.25,
                    assessment_weight=0.15,
                    passing_threshold=70.0,
                    is_active=True,
                )
                db.add(rule)
                db.flush()

            cls.validate_rule_weights(rule)

            candidate_skills = (
                db.query(CandidateSkill)
                .filter(
                    CandidateSkill.candidate_id == candidate.candidate_id
                )
                .all()
            )

            required_skills = (
                db.query(RequisitionRequiredSkill)
                .filter(
                    RequisitionRequiredSkill.requisition_id
                    == requisition.requisition_id
                )
                .all()
            )

            skill_score, skill_reasons = cls.calculate_skills_score(
                candidate_skills,
                required_skills,
            )

            experience_score, experience_reasons = (
                cls.calculate_experience_score(
                    candidate.total_experience_years,
                    requisition.min_experience_years,
                )
            )

            normalized_assessment = float(assessment_score)

            final_score = round(
                skill_score * float(rule.skill_weight)
                + experience_score * float(rule.experience_weight)
                + normalized_assessment
                * float(rule.assessment_weight),
                2,
            )
            final_score = min(100.0, max(0.0, final_score))

            decision = (
                "PASS"
                if final_score >= float(rule.passing_threshold)
                else "FAIL"
            )

            reason_codes = skill_reasons + experience_reasons
            reason_codes.append(
                "SURPASSED_PASSING_THRESHOLD"
                if decision == "PASS"
                else "FAILED_PASSING_THRESHOLD"
            )

            result = CandidateScreeningResult(
                application_id=application.application_id,
                rule_version=rule.rule_version,
                skill_match_score=skill_score,
                experience_score=experience_score,
                assessment_score=normalized_assessment,
                final_score=final_score,
                threshold=float(rule.passing_threshold),
                decision=decision,
                reason_codes_json=json.dumps(reason_codes),
                evaluated_at=eval_time,
            )
            db.add(result)

            application.screening_score = final_score
            application.decision_reason = (
                f"Screening {decision} "
                f"(Score: {final_score:.1f}/"
                f"{float(rule.passing_threshold):.1f})"
            )
            application.updated_at = eval_time

            previous_stage = application.current_stage

            event = ApplicationEvent(
                application_id=application.application_id,
                from_stage=(
                    previous_stage.value
                    if hasattr(previous_stage, "value")
                    else str(previous_stage)
                ),
                to_stage=ApplicationStage.SCREENING.value,
                actor=actor.strip(),
                reason=(
                    f"Application evaluated with score "
                    f"{final_score:.1f} ({decision})"
                ),
                rule_version=rule.rule_version,
                event_timestamp=eval_time,
            )

            db.add(event)
            application.current_stage = ApplicationStage.SCREENING

            db.commit()
            db.refresh(result)

            logger.info(
                "Screened application %s: decision=%s, score=%.2f",
                application.application_id,
                decision,
                final_score,
            )

            return result

        except ScreeningError:
            db.rollback()
            raise
        except Exception as exc:
            db.rollback()
            logger.exception(
                "Unexpected error while screening application %s",
                application_id,
            )
            raise ScreeningError(
                "Application screening failed due to a database "
                "or internal processing error."
            ) from exc
