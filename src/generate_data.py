import os
import sys
import json
import random
import hashlib
import argparse
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Tuple
import pandas as pd
import numpy as np
from faker import Faker

from src.database import get_db_context, init_db, reset_db_for_test
from src.models import (
    Department,
    JobRequisition,
    Candidate,
    Application,
    ResumeArtifact,
    Skill,
    CandidateSkill,
    DuplicateApplicationAttempt,
    RequisitionRequiredSkill,
    ScreeningRule,
    CandidateScreeningResult,
    Interviewer,
    Interview,
    InterviewerAssignment,
    Feedback,
    Offer,
    OfferApproval,
    RequisitionApproval,
    ApplicationEvent,
    AuditEvent,
    AnomalyRecord,
    RequisitionStatus,
    ApplicationStage,
    RoundType,
    InterviewStatus,
    RecommendationEnum,
    OfferStatus,
    ApprovalStatus,
    AnomalySeverity,
    AnomalyDetectionResult,
)
from src.screening import ScreeningEngine
from src.audit import AuditService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("recruitment_system.generator")


class SyntheticDataGenerator:
    """Deterministic, configurable generator for recruitment baseline and controlled anomaly datasets."""

    def __init__(self, seed: int = 20261022, scale: str = "full", output_dir: str = "data/generated"):
        self.seed = seed
        self.scale = scale.lower()
        self.output_dir = output_dir
        self.ground_truth_dir = "data/ground_truth"

        # Deterministic RNG initialization
        random.seed(self.seed)
        np.random.seed(self.seed)
        self.fake = Faker()
        Faker.seed(self.seed)

        # Scale configuration
        if self.scale == "starter":
            self.target_requisitions = 10
            self.target_candidates = 100
            self.target_applications = 150
            self.target_interviews = 30
            self.target_offers = 10
            self.dept_count = 5
            self.interviewer_count = 15
        else:  # full
            self.target_requisitions = 100
            self.target_candidates = 2000
            self.target_applications = 3000
            self.target_interviews = 600
            self.target_offers = 150
            self.dept_count = 8
            self.interviewer_count = 60

        self.base_time = datetime(2026, 1, 15, 9, 0, 0)

    def _hash_string(self, val: str) -> str:
        return hashlib.sha256(val.encode("utf-8")).hexdigest()

    def generate_and_seed(self, db_session) -> Dict[str, Any]:
        """Generates valid baseline dataset, inserts to database, injects controlled anomalies, and exports files."""
        logger.info(f"Starting deterministic data generation (Seed={self.seed}, Scale={self.scale})...")
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.ground_truth_dir, exist_ok=True)

        # Deterministic reseed
        random.seed(self.seed)
        np.random.seed(self.seed)
        Faker.seed(self.seed)
        self.fake = Faker()
        self.fake.seed_instance(self.seed)

        # 1. Master Departments
        dept_data = [
            ("ENG", "Software Engineering", "CC-1010"),
            ("PROD", "Product Management", "CC-1020"),
            ("DATA", "Data & Artificial Intelligence", "CC-1030"),
            ("DES", "Design & UX", "CC-1040"),
            ("SEC", "Information Security", "CC-1050"),
            ("OPS", "Cloud & Infrastructure Operations", "CC-1060"),
            ("QA", "Quality Assurance & Test Engineering", "CC-1070"),
            ("CORP", "Corporate & People Operations", "CC-1080"),
        ][:self.dept_count]

        departments: List[Department] = []
        for code, name, cc in dept_data:
            dept = Department(code=code, name=name, cost_center=cc, created_at=self.base_time, updated_at=self.base_time)
            db_session.add(dept)
            departments.append(dept)
        db_session.flush()

        # 2. Master Skills
        skill_catalog = [
            ("Python", "Backend"), ("SQL", "Database"), ("FastAPI", "Backend"), ("Docker", "Cloud"),
            ("Kubernetes", "Cloud"), ("AWS", "Cloud"), ("PostgreSQL", "Database"), ("MySQL", "Database"),
            ("React", "Frontend"), ("TypeScript", "Frontend"), ("Next.js", "Frontend"), ("System Design", "Architecture"),
            ("Pandas", "Data"), ("NumPy", "Data"), ("Machine Learning", "Data"), ("PyTest", "Testing"),
            ("Selenium", "Testing"), ("CI/CD", "DevOps"), ("Terraform", "DevOps"), ("Redis", "Database"),
            ("Microservices", "Architecture"), ("GraphQL", "API"), ("REST API", "API"), ("Git", "Tools"),
            ("Kafka", "Messaging"), ("Linux", "OS"), ("Go", "Backend"), ("Java", "Backend"),
            ("Agile Scrum", "Management"), ("Data Warehousing", "Data")
        ]
        skills: List[Skill] = []
        for s_name, s_cat in skill_catalog:
            skill = Skill(name=s_name, category=s_cat, created_at=self.base_time)
            db_session.add(skill)
            skills.append(skill)
        db_session.flush()

        # 3. Interviewers
        interviewers: List[Interviewer] = []
        titles = ["Senior Engineer", "Staff Engineer", "Engineering Manager", "Principal Architect", "QA Lead", "Tech Director"]
        for i in range(1, self.interviewer_count + 1):
            emp_id = f"EMP-{i:06d}"
            dept = departments[(i - 1) % len(departments)]
            interviewer = Interviewer(
                interviewer_id=emp_id,
                name=f"Interviewer {self.fake.first_name()} {self.fake.last_name()}",
                email=f"evaluator.{i:04d}@{dept.code.lower()}.yottaflex.internal",
                department_id=dept.id,
                title=titles[(i - 1) % len(titles)],
                is_active=True,
                created_at=self.base_time,
            )
            db_session.add(interviewer)
            interviewers.append(interviewer)
        db_session.flush()

        # 4. Job Requisitions (Target count)
        requisitions: List[JobRequisition] = []
        req_titles = [
            "Senior Backend Engineer (Python)", "Full Stack Developer", "Data Platform Engineer",
            "Cloud Infrastructure Architect", "QA Automation Engineer", "Product Manager - Core Platform",
            "Senior Site Reliability Engineer", "Frontend Specialist (React)", "Security Operations Engineer",
            "Database Administrator (MySQL)"
        ]
        for i in range(1, self.target_requisitions + 1):
            req_id = f"REQ-2026-{i:06d}"
            dept = departments[(i - 1) % len(departments)]
            min_sal = round(random.uniform(90000, 140000), -3)
            max_sal = min_sal + round(random.uniform(30000, 60000), -3)
            min_exp = float(random.choice([2.0, 3.0, 5.0, 7.0]))
            
            # 85% OPEN, 10% FILLED, 5% CLOSED
            r_val = random.random()
            if r_val < 0.85:
                status = RequisitionStatus.OPEN
                opened_at = self.base_time + timedelta(days=(i % 15))
                closed_at = None
            elif r_val < 0.95:
                status = RequisitionStatus.FILLED
                opened_at = self.base_time + timedelta(days=(i % 10))
                closed_at = opened_at + timedelta(days=20)
            else:
                status = RequisitionStatus.CLOSED
                opened_at = self.base_time + timedelta(days=(i % 10))
                closed_at = opened_at + timedelta(days=25)

            req = JobRequisition(
                requisition_id=req_id,
                title=req_titles[(i - 1) % len(req_titles)],
                department_id=dept.id,
                hiring_manager_id=interviewers[(i - 1) % len(interviewers)].interviewer_id,
                status=status,
                headcount=random.choice([1, 2, 3]),
                min_experience_years=min_exp,
                min_salary=min_sal,
                max_salary=max_sal,
                currency="USD",
                location=random.choice(["Remote", "San Francisco, CA", "Austin, TX", "New York, NY"]),
                opened_at=opened_at,
                closed_at=closed_at,
                created_at=self.base_time,
                updated_at=opened_at,
            )
            db_session.add(req)
            requisitions.append(req)
        db_session.flush()

        # Requisition Required Skills & Screening Rules
        req_to_skills = {}
        for req in requisitions:
            # Attach 2-3 required skills
            req_skill_sample = sorted(random.sample(skills, random.randint(2, 3)), key=lambda s: s.skill_id)
            req_to_skills[req.requisition_id] = req_skill_sample
            for s in req_skill_sample:
                r_skill = RequisitionRequiredSkill(
                    requisition_id=req.requisition_id,
                    skill_id=s.skill_id,
                    is_required=True,
                    min_experience_years=max(1.0, req.min_experience_years * 0.5),
                )
                db_session.add(r_skill)

            # Screening rule (weights sum strictly to 1.0)
            rule = ScreeningRule(
                requisition_id=req.requisition_id,
                rule_version="1.0",
                skill_weight=0.60,
                experience_weight=0.25,
                assessment_weight=0.15,
                passing_threshold=70.0,
                is_active=True,
                created_at=self.base_time,
            )
            db_session.add(rule)
        db_session.flush()

        # 5. Candidates (Target count, no protected demographics)
        candidates: List[Candidate] = []
        for i in range(1, self.target_candidates + 1):
            cand_id = f"CAND-{i:06d}"
            f_name = self.fake.first_name()
            l_name = self.fake.last_name()
            cand_email = f"candidate.{i:06d}.{f_name.lower()}@synthetic-talent.org"
            exp_years = round(random.uniform(2.0, 15.0), 1)

            cand = Candidate(
                candidate_id=cand_id,
                first_name=f_name,
                last_name=l_name,
                email=cand_email,
                phone=f"+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
                location=random.choice(["Austin, TX", "Seattle, WA", "Boston, MA", "Denver, CO", "Chicago, IL"]),
                total_experience_years=exp_years,
                created_at=self.base_time + timedelta(hours=(i % 120)),
                updated_at=self.base_time + timedelta(hours=(i % 120)),
            )
            db_session.add(cand)
            candidates.append(cand)
        db_session.flush()

        skill_by_id = {s.skill_id: s for s in skills}
        sorted_skills = sorted(skills, key=lambda s: s.skill_id)

        # Candidate Skills & Resumes
        for i, cand in enumerate(candidates):
            # Include skills from primary and secondary matching requisitions to guarantee qualified pool
            matched_req1 = requisitions[i % len(requisitions)]
            matched_req2 = requisitions[(i + 1) % len(requisitions)]
            needed_ids = sorted(list(set(
                [s.skill_id for s in req_to_skills[matched_req1.requisition_id]] +
                [s.skill_id for s in req_to_skills[matched_req2.requisition_id]]
            )))
            needed_skills = [skill_by_id[sid] for sid in needed_ids]
            extra_skills = [s for s in sorted_skills if s.skill_id not in set(needed_ids)]
            extra_sample = sorted(random.sample(extra_skills, random.randint(2, 4)), key=lambda s: s.skill_id)
            cand_skill_sample = needed_skills + extra_sample

            assigned_skill_names = []
            for s in cand_skill_sample:
                prof = random.randint(3, 5)
                s_years = min(cand.total_experience_years, round(random.uniform(2.0, cand.total_experience_years + 0.5), 1))
                cs = CandidateSkill(
                    candidate_id=cand.candidate_id,
                    skill_id=s.skill_id,
                    proficiency_level=prof,
                    years_experience=s_years,
                )
                db_session.add(cs)
                assigned_skill_names.append(s.name)

            # Resume artifact
            res_summary = (
                f"Professional summary for {cand.first_name} {cand.last_name}: Experienced technologist with "
                f"{cand.total_experience_years} years background in {', '.join(assigned_skill_names[:3])}. "
                f"Track record of scaling distributed web services and maintaining high availability."
            )
            resume = ResumeArtifact(
                candidate_id=cand.candidate_id,
                file_name=f"resume_{cand.candidate_id}.pdf",
                file_hash=self._hash_string(res_summary),
                resume_text_summary=res_summary,
                parsed_skills_json=json.dumps(assigned_skill_names),
                education_level=random.choice(["Bachelor of Science", "Master of Science", "Bachelor of Engineering"]),
                years_experience=cand.total_experience_years,
                created_at=cand.created_at,
            )
            db_session.add(resume)
        db_session.flush()

        # 6. Applications (Target count)
        # Pair candidates with matching and related requisitions deterministically
        applications: List[Application] = []
        app_pairs_seen = set()
        apps_needed = self.target_applications

        # Pass 1: Primary applications to matched requisitions
        for cand_idx in range(len(candidates)):
            if len(applications) >= apps_needed:
                break
            c = candidates[cand_idx]
            r = requisitions[cand_idx % len(requisitions)]
            pair = (r.requisition_id, c.candidate_id)
            if pair not in app_pairs_seen:
                app_pairs_seen.add(pair)
                app_id = f"APP-{r.requisition_id}-{c.candidate_id}"
                applied_time = (r.opened_at or self.base_time) + timedelta(days=1, hours=(cand_idx % 12))
                app = Application(
                    application_id=app_id,
                    candidate_id=c.candidate_id,
                    requisition_id=r.requisition_id,
                    current_stage=ApplicationStage.APPLIED,
                    applied_at=applied_time,
                    updated_at=applied_time,
                )
                db_session.add(app)
                applications.append(app)

        # Pass 2: Secondary cross-applications until apps_needed target reached
        offset = 1
        cand_idx = 0
        while len(applications) < apps_needed:
            c = candidates[cand_idx % len(candidates)]
            r = requisitions[(cand_idx + offset) % len(requisitions)]
            pair = (r.requisition_id, c.candidate_id)
            if pair not in app_pairs_seen:
                app_pairs_seen.add(pair)
                app_id = f"APP-{r.requisition_id}-{c.candidate_id}"
                applied_time = (r.opened_at or self.base_time) + timedelta(days=2, hours=(len(applications) % 12))
                app = Application(
                    application_id=app_id,
                    candidate_id=c.candidate_id,
                    requisition_id=r.requisition_id,
                    current_stage=ApplicationStage.APPLIED,
                    applied_at=applied_time,
                    updated_at=applied_time,
                )
                db_session.add(app)
                applications.append(app)

            cand_idx += 1
            if cand_idx % len(candidates) == 0:
                offset += 1
        db_session.flush()

        # 7. Screening Evaluation for Applications
        # Screen all applications through documented ScreeningEngine
        passed_apps: List[Application] = []
        for app in applications:
            # Deterministic assessment simulation (60..95)
            cand_seed_num = int(app.candidate_id.split("-")[-1])
            simulated_assessment = 65.0 + ((cand_seed_num * 17) % 35)
            
            res = ScreeningEngine.evaluate_application(
                db=db_session,
                application_id=app.application_id,
                assessment_score=simulated_assessment,
                actor="AUTO_SCREENER_SERVICE",
                evaluated_at=app.applied_at + timedelta(days=1),
            )
            if res.decision == "PASS":
                passed_apps.append(app)

        db_session.flush()
        logger.info(f"Screened {len(applications)} applications. Passed: {len(passed_apps)}.")

        # 8. Interviews (Target count)
        interviews: List[Interview] = []
        interviews_to_create = min(self.target_interviews, len(passed_apps))
        interview_candidates = passed_apps[:interviews_to_create]

        round_types = [RoundType.TECHNICAL, RoundType.SYSTEM_DESIGN, RoundType.BEHAVIORAL, RoundType.HR]
        for idx, app in enumerate(interview_candidates, start=1):
            int_id = f"INT-2026-{idx:06d}"
            app.current_stage = ApplicationStage.INTERVIEW
            app.updated_at = app.applied_at + timedelta(days=2)

            start_t = app.applied_at + timedelta(days=3, hours=(idx % 6) + 10)
            end_t = start_t + timedelta(hours=1)
            r_type = round_types[(idx - 1) % len(round_types)]

            intv = Interview(
                interview_id=int_id,
                application_id=app.application_id,
                round_number=1,
                round_type=r_type,
                scheduled_start=start_t,
                scheduled_end=end_t,
                status=InterviewStatus.COMPLETED,
                created_at=app.applied_at + timedelta(days=2),
                updated_at=end_t,
            )
            db_session.add(intv)
            interviews.append(intv)

            # Assign 2 interviewers per interview
            assigned_emps = [
                interviewers[(idx - 1) % len(interviewers)],
                interviewers[idx % len(interviewers)]
            ]
            for emp in assigned_emps:
                assign = InterviewerAssignment(
                    interview_id=intv.interview_id,
                    interviewer_id=emp.interviewer_id,
                    assigned_at=intv.created_at,
                )
                db_session.add(assign)

                # Valid Feedback Submission
                fb_id = f"FB-{intv.interview_id}-{emp.interviewer_id}"
                tech_r = min(5, max(1, 3 + ((idx + int(emp.interviewer_id[-2:])) % 3)))
                comm_r = min(5, max(1, 3 + ((idx * 2) % 3)))
                prob_r = min(5, max(1, 4))
                ov_score = round(tech_r * 0.4 + comm_r * 0.3 + prob_r * 0.3, 2)
                rec = RecommendationEnum.STRONG_HIRE if ov_score >= 4.0 else (RecommendationEnum.HIRE if ov_score >= 3.0 else RecommendationEnum.NO_HIRE)

                fb = Feedback(
                    feedback_id=fb_id,
                    interview_id=intv.interview_id,
                    interviewer_id=emp.interviewer_id,
                    technical_rating=tech_r,
                    communication_rating=comm_r,
                    problem_solving_rating=prob_r,
                    overall_score=ov_score,
                    recommendation=rec,
                    notes=f"Demonstrated solid competency during {r_type.value} round. Clear articulation of trade-offs.",
                    version=1,
                    submitted_at=end_t + timedelta(hours=1),
                    updated_at=end_t + timedelta(hours=1),
                )
                db_session.add(fb)

        db_session.flush()

        # Advance interviewed applications with feedback to DECISION_PENDING / OFFER_PENDING_APPROVAL
        for intv in interviews:
            app = db_session.query(Application).filter(Application.application_id == intv.application_id).first()
            app.current_stage = ApplicationStage.DECISION_PENDING
            app.updated_at = intv.scheduled_end + timedelta(hours=2)

        db_session.flush()

        # 9. Offers (Target count)
        offers: List[Offer] = []
        offers_to_create = min(self.target_offers, len(interviews))
        offer_apps = interviews[:offers_to_create]

        for idx, intv in enumerate(offer_apps, start=1):
            app = db_session.query(Application).filter(Application.application_id == intv.application_id).first()
            req = db_session.query(JobRequisition).filter(JobRequisition.requisition_id == app.requisition_id).first()
            off_id = f"OFF-2026-{idx:06d}"

            # Ensure valid baseline salary within requisition band
            base_sal = round(req.min_salary + (req.max_salary - req.min_salary) * 0.5, -2)
            issued_time = intv.scheduled_end + timedelta(days=2)
            expiry_time = issued_time + timedelta(days=7)

            # Determine realistic offer outcomes
            if idx <= int(offers_to_create * 0.65):
                status = OfferStatus.ACCEPTED
                resp_time = issued_time + timedelta(days=3)
                app.current_stage = ApplicationStage.ACCEPTED
                app.updated_at = resp_time
            elif idx <= int(offers_to_create * 0.85):
                status = OfferStatus.REJECTED
                resp_time = issued_time + timedelta(days=4)
                app.current_stage = ApplicationStage.OFFER_REJECTED
                app.updated_at = resp_time
            elif idx <= int(offers_to_create * 0.95):
                status = OfferStatus.EXPIRED
                resp_time = expiry_time + timedelta(hours=1)
                app.current_stage = ApplicationStage.OFFER_EXPIRED
                app.updated_at = resp_time
            else:
                status = OfferStatus.ISSUED
                resp_time = None
                app.current_stage = ApplicationStage.OFFERED
                app.updated_at = issued_time

            offer = Offer(
                offer_id=off_id,
                application_id=app.application_id,
                base_salary=base_sal,
                sign_on_bonus=10000.0,
                equity_shares=1500,
                currency=req.currency,
                status=status,
                is_out_of_band=False,
                exception_approved_by=None,
                issued_at=issued_time,
                expires_at=expiry_time,
                responded_at=resp_time,
                created_at=intv.scheduled_end + timedelta(days=1),
                updated_at=resp_time or issued_time,
            )
            db_session.add(offer)
            offers.append(offer)

            # Offer Approval Record
            approval = OfferApproval(
                offer_id=offer.offer_id,
                approver_id=req.hiring_manager_id,
                status=ApprovalStatus.APPROVED,
                comments="Approved standard market compensation offer.",
                decided_at=intv.scheduled_end + timedelta(days=1, hours=2),
                created_at=intv.scheduled_end + timedelta(days=1),
            )
            db_session.add(approval)

        db_session.commit()
        logger.info(f"Generated baseline data: {len(requisitions)} Reqs, {len(candidates)} Candidates, {len(applications)} Apps, {len(interviews)} Interviews, {len(offers)} Offers.")

        # 10. Inject Controlled Anomalies (Kept strictly separate, documented in ground truth)
        ground_truth_records = self._inject_controlled_anomalies(db_session, requisitions, candidates, applications, interviewers)

        # 11. Export Datasets to CSV and JSON
        self._export_datasets(db_session)
        self._export_ground_truth(ground_truth_records)

        return {
            "requisitions": len(requisitions),
            "candidates": len(candidates),
            "applications": len(applications),
            "interviews": len(interviews),
            "offers": len(offers),
            "anomalies": len(ground_truth_records),
        }

    def _inject_controlled_anomalies(
        self,
        db_session,
        requisitions: List[JobRequisition],
        candidates: List[Candidate],
        applications: List[Application],
        interviewers: List[Interviewer],
    ) -> List[Dict[str, Any]]:
        """
        Injects controlled anomaly records for all 5 required scenarios:
        1. INTERVIEWER_UNAVAILABLE
        2. DUPLICATE_APPLICATION
        3. MISSING_FEEDBACK
        4. SALARY_OUTSIDE_BAND
        5. CLOSED_ROLE_ACTIVE_APPLICATIONS
        """
        logger.info("Injecting controlled anomaly test records...")
        ground_truth: List[Dict[str, Any]] = []

        # Anomaly 1: INTERVIEWER_UNAVAILABLE
        # Set an interviewer to inactive and assign to a scheduled interview
        target_emp = interviewers[-1]
        target_emp.is_active = False
        target_app = applications[-1]
        anom_int_id = "INT-2026-999001"
        intv_anom = Interview(
            interview_id=anom_int_id,
            application_id=target_app.application_id,
            round_number=1,
            round_type=RoundType.TECHNICAL,
            scheduled_start=self.base_time + timedelta(days=20, hours=10),
            scheduled_end=self.base_time + timedelta(days=20, hours=11),
            status=InterviewStatus.SCHEDULED,
            created_at=self.base_time + timedelta(days=19),
            updated_at=self.base_time + timedelta(days=19),
        )
        db_session.add(intv_anom)
        assign = InterviewerAssignment(
            interview_id=anom_int_id,
            interviewer_id=target_emp.interviewer_id,
            assigned_at=self.base_time + timedelta(days=19),
        )
        db_session.add(assign)
        ground_truth.append({
            "issue_id": "ANOM-2026-000001",
            "issue_type": "INTERVIEWER_UNAVAILABLE",
            "affected_entity_type": "INTERVIEW",
            "affected_record_id": anom_int_id,
            "expected_decision": "BLOCK_ASSIGNMENT_OR_RESCHEDULE",
            "severity": "HIGH",
            "detection_result": "DETECTED_IN_AUDIT",
            "explanation": f"Interview {anom_int_id} assigned to inactive interviewer {target_emp.interviewer_id}.",
            "recommended_action": "Reassign to an active interviewer.",
        })

        # Anomaly 2: DUPLICATE_APPLICATION
        # Candidate submits another application for the same requisition; preserved in staging
        dup_cand = candidates[0]
        dup_req = requisitions[0]
        dup_attempt_id = f"APP-{dup_req.requisition_id}-{dup_cand.candidate_id}-DUP-01"
        dup_attempt = DuplicateApplicationAttempt(
            attempt_id=dup_attempt_id,
            candidate_id=dup_cand.candidate_id,
            requisition_id=dup_req.requisition_id,
            status="BLOCKED_DUPLICATE",
            attempted_at=self.base_time + timedelta(days=15),
            reason="Blocked by unique constraint: Candidate already applied to this requisition",
        )
        db_session.add(dup_attempt)
        ground_truth.append({
            "issue_id": "ANOM-2026-000002",
            "issue_type": "DUPLICATE_APPLICATION",
            "affected_entity_type": "APPLICATION",
            "affected_record_id": dup_attempt_id,
            "expected_decision": "REJECT_OR_FLAG_DUPLICATE_ATTEMPT",
            "severity": "MEDIUM",
            "detection_result": "BLOCKED_BY_VALIDATION",
            "explanation": f"Duplicate application attempt {dup_attempt_id} by candidate {dup_cand.candidate_id} for {dup_req.requisition_id} blocked and recorded in staging.",
            "recommended_action": "Consolidate duplicate records and preserve staging attempt logs.",
        })

        # Anomaly 3: MISSING_FEEDBACK
        # Application advanced to DECISION_PENDING despite missing required interviewer feedback
        missing_fb_app = applications[-2]
        missing_fb_int_id = "INT-2026-999002"
        missing_fb_app.current_stage = ApplicationStage.DECISION_PENDING
        missing_fb_app.updated_at = self.base_time + timedelta(days=12, hours=16)
        intv_missing = Interview(
            interview_id=missing_fb_int_id,
            application_id=missing_fb_app.application_id,
            round_number=1,
            round_type=RoundType.SYSTEM_DESIGN,
            scheduled_start=self.base_time + timedelta(days=12, hours=14),
            scheduled_end=self.base_time + timedelta(days=12, hours=15),
            status=InterviewStatus.COMPLETED,
            created_at=self.base_time + timedelta(days=11),
            updated_at=self.base_time + timedelta(days=12, hours=15),
        )
        db_session.add(intv_missing)
        assign_missing = InterviewerAssignment(
            interview_id=missing_fb_int_id,
            interviewer_id=interviewers[0].interviewer_id,
            assigned_at=self.base_time + timedelta(days=11),
        )
        db_session.add(assign_missing)
        # Deliberately do NOT add Feedback record for assign_missing
        ground_truth.append({
            "issue_id": "ANOM-2026-000003",
            "issue_type": "MISSING_FEEDBACK",
            "affected_entity_type": "APPLICATION",
            "affected_record_id": missing_fb_app.application_id,
            "expected_decision": "BLOCK_ADVANCEMENT_UNTIL_FEEDBACK_SUBMITTED",
            "severity": "HIGH",
            "detection_result": "DETECTED_IN_AUDIT",
            "explanation": f"Application {missing_fb_app.application_id} advanced without scorecard from {interviewers[0].interviewer_id}.",
            "recommended_action": "Collect missing scorecard or revert stage.",
        })

        # Anomaly 4: SALARY_OUTSIDE_BAND
        # Offer exceeds approved requisition max salary without authorized exception
        target_off_app = applications[-3]
        target_off_req = db_session.query(JobRequisition).filter(JobRequisition.requisition_id == target_off_app.requisition_id).first()
        excessive_sal = target_off_req.max_salary + 45000.0  # Well over max
        anom_off_id = "OFF-2026-999001"
        out_of_band_off = Offer(
            offer_id=anom_off_id,
            application_id=target_off_app.application_id,
            base_salary=excessive_sal,
            sign_on_bonus=20000.0,
            equity_shares=5000,
            currency="USD",
            status=OfferStatus.ISSUED,
            is_out_of_band=True,
            exception_approved_by=None,  # Missing approval!
            issued_at=self.base_time + timedelta(days=18),
            expires_at=self.base_time + timedelta(days=25),
            created_at=self.base_time + timedelta(days=17),
            updated_at=self.base_time + timedelta(days=18),
        )
        db_session.add(out_of_band_off)
        ground_truth.append({
            "issue_id": "ANOM-2026-000004",
            "issue_type": "SALARY_OUTSIDE_BAND",
            "affected_entity_type": "OFFER",
            "affected_record_id": anom_off_id,
            "expected_decision": "BLOCK_OFFER_OR_REQUIRE_EXECUTIVE_APPROVAL",
            "severity": "HIGH",
            "detection_result": "DETECTED_IN_AUDIT",
            "explanation": f"Offer {anom_off_id} salary (${excessive_sal:,.2f}) exceeds req limit (${target_off_req.max_salary:,.2f}) without exception approval.",
            "recommended_action": "Obtain executive approval or reduce offer salary.",
        })

        # Anomaly 5: CLOSED_ROLE_ACTIVE_APPLICATIONS
        # Requisition is closed while applications remain active in APPLIED / SCREENING
        active_app_on_closed_role = applications[5] if len(applications) > 5 else applications[0]
        closed_req = db_session.query(JobRequisition).filter(
            JobRequisition.requisition_id == active_app_on_closed_role.requisition_id
        ).first()
        closed_req.status = RequisitionStatus.CLOSED
        closed_req.closed_at = self.base_time + timedelta(days=15)
        closed_req.updated_at = self.base_time + timedelta(days=15)
        active_app_on_closed_role.current_stage = ApplicationStage.APPLIED
        active_app_on_closed_role.updated_at = self.base_time + timedelta(days=15)
        
        ground_truth.append({
            "issue_id": "ANOM-2026-000005",
            "issue_type": "CLOSED_ROLE_ACTIVE_APPLICATIONS",
            "affected_entity_type": "APPLICATION",
                "affected_record_id": active_app_on_closed_role.application_id,
                "expected_decision": "DISPOSITION_APPLICATIONS_BEFORE_CLOSING_REQUISITION",
                "severity": "MEDIUM",
                "detection_result": "DETECTED_IN_AUDIT",
                "explanation": f"Application {active_app_on_closed_role.application_id} active under closed requisition {closed_req.requisition_id}.",
                "recommended_action": "Disposition active candidates before finalizing role closure.",
            })

        db_session.commit()
        return ground_truth

    def _export_datasets(self, db_session):
        """Exports all database tables to deterministic CSV and JSON files."""
        logger.info(f"Exporting database tables to {self.output_dir}...")
        tables = [
            ("departments", Department),
            ("skills", Skill),
            ("interviewers", Interviewer),
            ("job_requisitions", JobRequisition),
            ("requisition_required_skills", RequisitionRequiredSkill),
            ("screening_rules", ScreeningRule),
            ("candidates", Candidate),
            ("candidate_skills", CandidateSkill),
            ("resume_artifacts", ResumeArtifact),
            ("applications", Application),
            ("duplicate_application_attempts", DuplicateApplicationAttempt),
            ("candidate_screening_results", CandidateScreeningResult),
            ("interviews", Interview),
            ("interviewer_assignments", InterviewerAssignment),
            ("feedback", Feedback),
            ("offers", Offer),
            ("offer_approvals", OfferApproval),
            ("application_events", ApplicationEvent),
            ("audit_events", AuditEvent),
        ]

        for table_name, model_cls in tables:
            rows = db_session.query(model_cls).all()
            data_list = []
            for r in rows:
                row_dict = {}
                for col in model_cls.__table__.columns:
                    val = getattr(r, col.name)
                    if isinstance(val, datetime):
                        val = val.isoformat()
                    elif hasattr(val, "value"):  # Enum
                        val = val.value
                    row_dict[col.name] = val
                data_list.append(row_dict)

            # Sort deterministically
            df = pd.DataFrame(data_list)
            if not df.empty:
                if "candidate_id" in df.columns and "skill_id" in df.columns:
                    df = df.sort_values(by=["candidate_id", "skill_id"])
                elif "requisition_id" in df.columns and "skill_id" in df.columns:
                    df = df.sort_values(by=["requisition_id", "skill_id"])
                elif "interview_id" in df.columns and "interviewer_id" in df.columns:
                    df = df.sort_values(by=["interview_id", "interviewer_id"])
                elif "requisition_id" in df.columns and "candidate_id" in df.columns:
                    df = df.sort_values(by=["requisition_id", "candidate_id"])
                elif "application_id" in df.columns and "round_number" in df.columns:
                    df = df.sort_values(by=["application_id", "round_number"])
                else:
                    sort_cols = [c for c in df.columns if c in ["requisition_id", "candidate_id", "interview_id", "offer_id", "id", "code", "name"]]
                    if sort_cols:
                        df = df.sort_values(by=sort_cols[:2])
                    else:
                        df = df.sort_values(by=df.columns[0])

            csv_path = os.path.join(self.output_dir, f"{table_name}.csv")
            json_path = os.path.join(self.output_dir, f"{table_name}.json")
            df.to_csv(csv_path, index=False)
            df.to_json(json_path, orient="records", indent=2)

        logger.info("Database tables exported successfully.")

    def _export_ground_truth(self, ground_truth: List[Dict[str, Any]]):
        """Exports anomaly ground truth to ground_truth.csv and ground_truth.json."""
        logger.info(f"Writing anomaly ground truth to {self.ground_truth_dir}...")
        df_gt = pd.DataFrame(ground_truth)
        csv_gt = os.path.join(self.ground_truth_dir, "ground_truth.csv")
        json_gt = os.path.join(self.ground_truth_dir, "ground_truth.json")
        df_gt.to_csv(csv_gt, index=False)
        with open(json_gt, "w", encoding="utf-8") as f:
            json.dump(ground_truth, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Deterministic Synthetic Recruitment Data Generator")
    parser.add_argument("--seed", type=int, default=20261022, help="Deterministic integer seed")
    parser.add_argument("--scale", type=str, default="full", choices=["starter", "full"], help="Dataset scale")
    parser.add_argument("--output-dir", type=str, default="data/generated", help="Target output folder")
    parser.add_argument("--reset-db", action="store_true", help="Reset database before seeding")
    args = parser.parse_args()

    init_db()
    with get_db_context() as session:
        if args.reset_db:
            reset_db_for_test()
        generator = SyntheticDataGenerator(seed=args.seed, scale=args.scale, output_dir=args.output_dir)
        summary = generator.generate_and_seed(session)
        print("\n=== Data Generation Summary ===")
        for k, v in summary.items():
            print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
