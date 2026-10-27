
import pytest

from src.offers import OfferService, OfferPolicyError
from src.models import (
    Department,
    JobRequisition,
    Candidate,
    Application,
    OfferStatus,
    ApplicationStage,
    RequisitionStatus,
    ApprovalStatus,
)


def test_salary_outside_band_requires_exception(test_db):
    """Verify out-of-band offers require explicit exception approval."""

    # Create department
    dept = Department(
        code="CORP",
        name="Corporate",
        cost_center="CC-900",
    )
    test_db.add(dept)
    test_db.flush()

    # Create requisition
    req = JobRequisition(
        requisition_id="REQ-2026-000400",
        title="Finance Director",
        department_id=dept.id,
        hiring_manager_id="EMP-000001",
        status=RequisitionStatus.OPEN,
        min_salary=150000.0,
        max_salary=200000.0,
    )

    # Create candidate
    cand = Candidate(
        candidate_id="CAND-000401",
        first_name="Robin",
        last_name="Hood",
        email="robin@corp.com",
        phone="1",
        location="L",
    )

    # Create application
    app = Application(
        application_id="APP-REQ-2026-000400-CAND-000401",
        candidate_id=cand.candidate_id,
        requisition_id=req.requisition_id,
        current_stage=ApplicationStage.OFFER_PENDING_APPROVAL,
    )

    test_db.add_all([req, cand, app])
    test_db.commit()

    # 1. Out-of-band offer without an approver must be rejected.
    with pytest.raises(
        OfferPolicyError,
        match="exceeds requisition maximum",
    ):
        OfferService.create_offer(
            db=test_db,
            offer_id="OFF-2026-000401",
            application_id=app.application_id,
            base_salary=240000.0,
        )

    # 2. An approver can be assigned to the exception request.
    offer_allowed = OfferService.create_offer(
        db=test_db,
        offer_id="OFF-2026-000402",
        application_id=app.application_id,
        base_salary=240000.0,
        approver_id="CFO_EXEC_01",
    )

    assert offer_allowed.is_out_of_band is True
    assert offer_allowed.status == OfferStatus.DRAFT

    # Assignment is not the same as approval.
    assert offer_allowed.exception_approved_by is None

    # 3. Explicit approval authorizes the salary exception.
    approved_offer = OfferService.approve_offer(
        db=test_db,
        offer_id=offer_allowed.offer_id,
        approver_id="CFO_EXEC_01",
        status=ApprovalStatus.APPROVED,
        comments="Authorized compensation exception",
    )

    assert approved_offer.status == OfferStatus.APPROVED
    assert approved_offer.exception_approved_by == "CFO_EXEC_01"


def test_offer_issuance_and_acceptance_lifecycle(test_db):
    """Test the offer lifecycle and requisition headcount update."""

    # Create department
    dept = Department(
        code="CORP",
        name="Corporate",
        cost_center="CC-900",
    )
    test_db.add(dept)
    test_db.flush()

    # Create requisition
    req = JobRequisition(
        requisition_id="REQ-2026-000403",
        title="Accountant",
        department_id=dept.id,
        hiring_manager_id="EMP-000001",
        status=RequisitionStatus.OPEN,
        headcount=1,
        min_salary=70000.0,
        max_salary=95000.0,
    )

    # Create candidate
    cand = Candidate(
        candidate_id="CAND-000402",
        first_name="Sam",
        last_name="Hill",
        email="sam@corp.com",
        phone="2",
        location="L",
    )

    # Create application
    app = Application(
        application_id="APP-REQ-2026-000403-CAND-000402",
        candidate_id=cand.candidate_id,
        requisition_id=req.requisition_id,
        current_stage=ApplicationStage.OFFER_PENDING_APPROVAL,
    )

    test_db.add_all([req, cand, app])
    test_db.commit()

    # 1. Create an in-band offer.
    offer = OfferService.create_offer(
        db=test_db,
        offer_id="OFF-2026-000403",
        application_id=app.application_id,
        base_salary=85000.0,
    )

    assert offer.status == OfferStatus.DRAFT

    # 2. An unapproved offer cannot be issued.
    with pytest.raises(OfferPolicyError, match="must be APPROVED"):
        OfferService.issue_offer(
            db=test_db,
            offer_id=offer.offer_id,
        )

    # 3. Approve the offer.
    OfferService.approve_offer(
        db=test_db,
        offer_id=offer.offer_id,
        approver_id="EMP-000001",
        status=ApprovalStatus.APPROVED,
    )

    test_db.refresh(offer)
    assert offer.status == OfferStatus.APPROVED

    # 4. Issue the approved offer.
    OfferService.issue_offer(
        db=test_db,
        offer_id=offer.offer_id,
    )

    test_db.refresh(offer)
    test_db.refresh(app)

    assert offer.status == OfferStatus.ISSUED
    assert app.current_stage == ApplicationStage.OFFERED

    # 5. Candidate accepts the offer.
    OfferService.record_candidate_decision(
        db=test_db,
        offer_id=offer.offer_id,
        decision="ACCEPTED",
    )

    test_db.refresh(offer)
    test_db.refresh(app)
    test_db.refresh(req)

    assert offer.status == OfferStatus.ACCEPTED
    assert app.current_stage == ApplicationStage.ACCEPTED

    # Headcount is one and has been filled.
    assert req.status == RequisitionStatus.FILLED
