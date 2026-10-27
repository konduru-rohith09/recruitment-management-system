import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database import Base
from src.models import (
    Department,
    JobRequisition,
    Candidate,
    Application,
    Skill,
    CandidateSkill,
    RequisitionRequiredSkill,
    ScreeningRule,
    Interviewer,
    Interview,
    InterviewerAssignment,
    Feedback,
    Offer,
    OfferApproval,
    RequisitionApproval,
    ApplicationEvent,
    AuditEvent,
    DuplicateApplicationAttempt,
    AnomalyRecord,
    RequisitionStatus,
    ApplicationStage,
    RoundType,
    InterviewStatus,
    OfferStatus,
    ApprovalStatus,
    RecommendationEnum,
    utc_now,
)

# In-memory SQLite engine for tests
TEST_DB_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def test_db():
    """Provides an isolated database session with freshly initialized schema for each test."""
    engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
