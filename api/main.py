
import logging
import os
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional

from fastapi import Depends, FastAPI, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.database import get_db, init_db
from src.metrics import MetricsCalculator
from src.audit import AuditService
from src.models import AnomalyRecord

from api.routes.requisitions import router as requisitions_router
from api.routes.applications import router as applications_router
from api.routes.interviews import router as interviews_router
from api.routes.offers import router as offers_router
from api.routes.candidates import router as candidates_router


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

logger = logging.getLogger("recruitment_system.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize application resources during startup."""
    try:
        init_db()
        logger.info("Recruitment API initialized successfully.")
        yield
    except Exception:
        logger.exception("Recruitment API startup or runtime failed.")
        raise


app = FastAPI(
    title="Recruitment Management & Workflow Validation System API",
    description=(
        "RESTful API for candidate lifecycle orchestration, "
        "interviewer scheduling, and compliance validation."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# CORS configuration.
# Configure allowed origins using CORS_ORIGINS in your .env file.
cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        (
            "http://localhost:5173,"
            "http://127.0.0.1:5173,"
            "http://localhost:3000,"
            "http://localhost:8501"
        ),
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)


# Register route modules.
app.include_router(requisitions_router)
app.include_router(applications_router)
app.include_router(interviews_router)
app.include_router(offers_router)
app.include_router(candidates_router)


@app.get("/", tags=["System Health"])
def root() -> Dict[str, str]:
    """Return basic API information."""
    return {
        "service": "recruitment-management-system",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.get(
    "/health",
    tags=["System Health"],
    status_code=status.HTTP_200_OK,
)
def health_check(
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Report API and database health."""
    try:
        db.execute(text("SELECT 1"))

        return {
            "status": "UP",
            "service": "recruitment-management-system",
            "database": "HEALTHY",
            "version": "1.0.0",
        }

    except Exception:
        logger.exception("Database health check failed.")

        return {
            "status": "DEGRADED",
            "service": "recruitment-management-system",
            "database": "UNHEALTHY",
            "version": "1.0.0",
        }


@app.get("/metrics", tags=["Analytics & KPIs"])
def get_metrics(
    department_id: Optional[int] = Query(
        None,
        ge=1,
        description="Filter metrics by department ID",
    ),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Compute hiring metrics and conversion funnels."""
    return MetricsCalculator.compute_all_metrics(
        db=db,
        department_id=department_id,
    )


@app.get("/anomalies", tags=["Compliance & Auditing"])
def get_anomalies(
    rescan: bool = Query(
        False,
        description="Trigger an audit scan across the database",
    ),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Retrieve detected anomalies across the required scenarios."""
    if rescan:
        anomalies = AuditService.scan_for_anomalies(db)
    else:
        anomalies = db.query(AnomalyRecord).all()

        if not anomalies:
            anomalies = AuditService.scan_for_anomalies(db)

    items = [
        {
            "issue_id": anomaly.issue_id,
            "issue_type": anomaly.issue_type,
            "affected_entity_type": anomaly.affected_entity_type,
            "affected_record_id": anomaly.affected_record_id,
            "expected_decision": anomaly.expected_decision,
            "severity": (
                anomaly.severity.value
                if hasattr(anomaly.severity, "value")
                else str(anomaly.severity)
            ),
            "detection_result": (
                anomaly.detection_result.value
                if hasattr(anomaly.detection_result, "value")
                else str(anomaly.detection_result)
            ),
            "explanation": anomaly.explanation,
            "recommended_action": anomaly.recommended_action,
            "detected_at": (
                anomaly.detected_at.isoformat()
                if anomaly.detected_at
                else None
            ),
        }
        for anomaly in anomalies
    ]

    return {
        "total_anomalies": len(items),
        "items": items,
    }
