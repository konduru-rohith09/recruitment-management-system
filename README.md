# Recruitment Management & Workflow Validation System

An enterprise-grade, deterministic talent acquisition workflow system built for the 72-hour engineering challenge. The system orchestrates end-to-end recruitment pipelines from job requisition approval to formal offer acceptance, enforces explainable screening criteria, detects compliance anomalies across 5 mandatory operational scenarios, and provides interactive analytics via FastAPI and Streamlit.

---

## 1. Project Objective

The recruitment management platform provides automated traceability, mathematical scoring, schedule conflict prevention, and tamper-resistant state machine progression:
- **Requisitions**: Headcount budgeting, salary bands, and executive approval chains.
- **Screening**: 100% job-related explainable scoring using weighted skill matching, verified experience, and assessments. Strictly excludes demographic or protected characteristics (age, gender, caste, religion, disability).
- **Scheduling**: Multi-interviewer calendar management with transactional overlap conflict prevention.
- **Workflow State Machine**: Finite-state machine tracking `APPLIED` through `ACCEPTED` with mandatory scorecard completion guards.
- **Compensation & Offers**: Enforces approved compensation bands and executive exception authorization.
- **Auditing & Compliance**: Real-time scanners that flag 5 core anomaly scenarios.
- **Reproducibility**: Fixed-seed deterministic synthetic generation producing bitwise-identical exports.

---

## 2. Technology Stack

- **Backend Runtime**: Python 3.11+
- **RESTful API**: FastAPI with OpenAPI/Swagger interactive documentation
- **Database Engine**: MySQL 8.0+ with InnoDB engine and `utf8mb4` encoding (SQLite supported for isolated unit testing)
- **Object-Relational Mapping (ORM)**: SQLAlchemy 2.x
- **Database Driver**: PyMySQL
- **Data Validation & Typing**: Pydantic v2
- **Data Science & Synthesis**: pandas, NumPy, Faker
- **Analytics & Dashboard**: Streamlit with interactive Plotly visual funnels
- **Test Suite**: pytest
- **Schema Migrations**: Alembic
- **Configuration Management**: python-dotenv

---

## 3. Architecture & Directory Structure

```
recruitment-management-system/
├── src/
│   ├── __init__.py
│   ├── models.py                     # 12 core entities, bridge tables, and anomaly records
│   ├── database.py                   # Engine initialization, connection pooling, session lifecycle
│   ├── generate_data.py              # Deterministic synthetic data generator (starter & full scales)
│   ├── screening.py                  # Configurable, explainable screening engine
│   ├── scheduling.py                 # Multi-interviewer scheduling with conflict detection
│   ├── workflow.py                   # Finite-state machine & structured feedback validator
│   ├── offers.py                     # Offer issuance, compensation bands, and decision lifecycle
│   ├── audit.py                      # Audit logging & automated anomaly detection scanner
│   ├── validation.py                 # 15+ integrity and constraint validation checks
│   ├── metrics.py                    # Zero-division-safe KPIs and conversion funnel formulas
│   └── services/
│       ├── __init__.py
│       ├── requisition_service.py    # Requisition domain service
│       ├── application_service.py    # Application lodgement & screening service
│       ├── interview_service.py      # Scheduling & scorecard service
│       └── offer_service.py          # Compensation & offer service
├── api/
│   ├── __init__.py
│   ├── main.py                       # FastAPI entrypoint, health, metrics & anomaly endpoints
│   └── routes/
│       ├── __init__.py
│       ├── requisitions.py           # Requisition REST endpoints
│       ├── applications.py           # Application & screening endpoints
│       ├── interviews.py             # Scheduling & feedback endpoints
│       └── offers.py                 # Offer lifecycle & approval endpoints
├── app/
│   ├── __init__.py
│   └── dashboard.py                  # Streamlit dashboard with Plotly hiring funnels & anomaly review
├── schemas/
│   ├── schema.sql                    # Production MySQL 8.0 DDL script with InnoDB & foreign keys
│   ├── data_dictionary.md            # Complete database dictionary with field specifications
│   └── relationships.md             # ER diagrams, bridge tables, and lifecycle transition matrix
├── data/
│   ├── generated/                    # Exported CSV and JSON baseline datasets
│   └── ground_truth/                 # Ground truth anomaly dataset (ground_truth.csv/json)
├── tests/
│   ├── __init__.py
│   ├── conftest.py                   # Pytest fixtures with isolated in-memory test database
│   ├── test_models.py                # Database models, constraints, and relationships
│   ├── test_generation.py            # Baseline row counts and synthetic data properties
│   ├── test_screening.py             # Scoring formulas, weight validation, and boundary conditions
│   ├── test_scheduling.py            # Scheduling conflicts and inactive interviewer detection
│   ├── test_workflow.py              # State transitions and missing feedback guards
│   ├── test_offers.py                # Salary band enforcement and candidate decisions
│   ├── test_validation.py            # DataValidator rules and zero-denominator safety
│   └── test_reproducibility.py       # Two-run bitwise SHA-256 reproducibility verification
├── reports/
│   ├── validation_summary.json       # Automated validation checks output
│   └── reproducibility_report.json   # Two-run verification report with file checksums
├── migrations/
│   ├── env.py                        # Alembic environment configuration
│   ├── script.py.mako                # Migration script template
│   └── versions/
├── alembic.ini                       # Alembic migration configuration
├── .env.example                      # Sample environment variables
├── .gitignore                        # Git exclusion rules
├── Dockerfile                        # Production container definition
├── requirements.txt                  # Locked Python dependencies
└── README.md                         # Project documentation
```

---

## 4. Deterministic Identifier Conventions

All entities across database tables, API payloads, and exported files use deterministic identifiers:
- **Job Requisition**: `REQ-YYYY-NNNNNN` (e.g. `REQ-2026-000001`)
- **Candidate**: `CAND-NNNNNN` (e.g. `CAND-000001`)
- **Application**: `APP-<requisition-id>-<candidate-id>` (e.g. `APP-REQ-2026-000001-CAND-000001`)
- **Interview**: `INT-YYYY-NNNNNN` (e.g. `INT-2026-000001`)
- **Feedback**: `FB-<interview-id>-<interviewer-id>` (e.g. `FB-INT-2026-000001-EMP-000001`)
- **Offer**: `OFF-YYYY-NNNNNN` (e.g. `OFF-2026-000001`)
- **Anomaly Issue**: `ANOM-YYYY-NNNNNN` (e.g. `ANOM-2026-000001`)

---

## 5. Local Setup & Installation

### Prerequisites
- Python 3.11+
- Git
- MySQL 8.0+ (Optional for local testing; SQLite is supported as fallback)

### 1. Clone & Set Up Environment
```bash
git clone <repository-url>
cd recruitment-management-system

# Create and activate virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Edit `.env` to configure your database connection:
```ini
# MySQL 8.0 Configuration
DATABASE_URL=mysql+pymysql://recruit_user:recruit_password@localhost:3306/recruitment_db?charset=utf8mb4

# Or SQLite Fallback (automatically used if DATABASE_URL is unset)
# DATABASE_URL=sqlite:///./data/recruitment.db
```

### 3. MySQL Database Setup (When running against MySQL)
Log in to MySQL as root and execute:
```sql
CREATE DATABASE recruitment_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'recruit_user'@'localhost' IDENTIFIED BY 'recruit_password';
GRANT ALL PRIVILEGES ON recruitment_db.* TO 'recruit_user'@'localhost';
FLUSH PRIVILEGES;
```
Initialize the schema either via Alembic or direct DDL:
```bash
# Option A: Alembic Migrations
alembic upgrade head

# Option B: Direct Schema Import
mysql -u recruit_user -p recruitment_db < schemas/schema.sql
```

---

## 6. Synthetic Data Generation

The deterministic synthetic data generator supports both starter and full scales using seed `20261022`.

### Starter Scale (Fast testing & CI)
```bash
python -m src.generate_data --seed 20261022 --scale starter --reset-db
```
**Expected Counts**:
- Requisitions: 10
- Candidates: 100
- Applications: 150
- Interviews: 30
- Offers: 10
- Controlled Anomalies: 5

### Full Scale (Complete benchmark challenge dataset)
```bash
python -m src.generate_data --seed 20261022 --scale full --reset-db
```
**Expected Counts**:
- Requisitions: 100
- Candidates: 2,000
- Applications: 3,000
- Interviews: 600
- Offers: 150
- Controlled Anomalies: 5

Outputs are exported as CSV and JSON into `data/generated/` and `data/ground_truth/`.

---

## 7. Running the Application

### 1. Start the FastAPI REST API
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive API documentation:
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- Health check: [http://localhost:8000/health](http://localhost:8000/health)
- Metrics: [http://localhost:8000/metrics](http://localhost:8000/metrics)
- Anomalies: [http://localhost:8000/anomalies](http://localhost:8000/anomalies)

### 2. Start the Streamlit Analytics Dashboard
```bash
streamlit run app/dashboard.py --server.port 8501
```
Dashboard features:
- **Top KPI Cards**: Total headcounts, active pipeline volume, screening pass rate, offer acceptance rate, anomaly counters.
- **Hiring Funnel**: Interactive Plotly conversion funnel tracking stages.
- **Requisitions & Stages**: Status distribution pie charts and horizontal stage histograms.
- **Interviews & Scorecards**: Completion rates, interviewer feedback breakdowns, rating distributions.
- **Anomaly Center**: Filterable table showing all 5 anomaly scenarios, severity ratings, and recommended corrective actions.
- **Validation Audit**: Live execution of data integrity checks with pass/fail reporting.

---

## 8. Business Rules & Anomaly Scenarios

The system enforces strict business logic and detects 5 core anomaly scenarios:

| Scenario Code | Affected Entity | Expected Decision | Severity | Enforcement / Audit Behavior |
|---|---|---|---|---|
| `INTERVIEWER_UNAVAILABLE` | Interview | `BLOCK_ASSIGNMENT_OR_RESCHEDULE` | HIGH / CRITICAL | Blocks booking if interviewer is inactive (`is_active=False`) or already assigned to an overlapping interview slot. |
| `DUPLICATE_APPLICATION` | Application | `REJECT_OR_FLAG_DUPLICATE_ATTEMPT` | MEDIUM | Preserves baseline application primary key and records duplicate attempts into `duplicate_application_attempts` staging ledger. |
| `MISSING_FEEDBACK` | Application | `BLOCK_ADVANCEMENT_UNTIL_FEEDBACK_SUBMITTED` | HIGH | Blocks candidate advancement to `DECISION_PENDING` until all assigned interviewers submit completed scorecards (1–5 ratings + notes). |
| `SALARY_OUTSIDE_BAND` | Offer | `BLOCK_OFFER_OR_REQUIRE_EXECUTIVE_APPROVAL` | HIGH | Blocks offer creation/issuance if base salary exceeds requisition `max_salary` unless an executive exception (`exception_approved_by`) is authorized. |
| `CLOSED_ROLE_ACTIVE_APPLICATIONS` | Requisition / Application | `DISPOSITION_APPLICATIONS_BEFORE_CLOSING_REQUISITION` | MEDIUM | Flags requisitions closed or cancelled while candidate applications remain in active stages (`APPLIED`, `SCREENING`, `INTERVIEW`, `OFFERED`). |

---

## 9. Metrics & KPI Definitions

All metrics are calculated directly from persisted database records with safe handling of empty denominators:

1. **Screening Pass Rate**:
   $$\text{Screening Pass Rate (\%)} = \left( \frac{\text{Passed Screenings}}{\text{Total Screened Applications}} \right) \times 100$$
2. **Average Screening Score**:
   $$\text{Average Screening Score} = \frac{\sum \text{Screening Final Scores}}{\text{Total Screened Applications}}$$
3. **Interview Completion Rate**:
   $$\text{Interview Completion Rate (\%)} = \left( \frac{\text{Completed Interviews}}{\text{Total Scheduled Interviews}} \right) \times 100$$
4. **Interviewer Feedback Submission Rate**:
   $$\text{Feedback Rate (\%)} = \left( \frac{\text{Submitted Scorecards}}{\text{Total Interviewer Assignments}} \right) \times 100$$
5. **Offer Acceptance Rate (Using Decided Offers as Denominator)**:
   $$\text{Offer Acceptance Rate (\%)} = \left( \frac{\text{Accepted Offers}}{\text{Accepted Offers} + \text{Rejected Offers} + \text{Expired Offers}} \right) \times 100$$
6. **Application Rejection Rate**:
   $$\text{Rejection Rate (\%)} = \left( \frac{\text{Rejected Applications} + \text{Offer Rejected Applications}}{\text{Total Applications}} \right) \times 100$$
7. **Application Withdrawal Rate**:
   $$\text{Withdrawal Rate (\%)} = \left( \frac{\text{Withdrawn Applications}}{\text{Total Applications}} \right) \times 100$$
8. **Average Time to Decision**:
   $$\text{Avg Days to Decision} = \frac{\sum (\text{Decision Date} - \text{Application Date})}{\text{Total Decided Applications}}$$

---

## 10. Automated Testing & Reproducibility Verification

Execute the complete pytest suite:
```bash
pytest -v
```

### Verification Results
- **19 of 19 tests passing** across 8 test suites.
- **Reproducibility Test (`tests/test_reproducibility.py`)**:
  - Two independent runs generated with seed `20261022`.
  - Bitwise SHA-256 content checksum comparison across all 17 exported tables.
  - Verification results written to `reports/reproducibility_report.json`.

---

## 11. Known Limitations

1. **Email / SMS Notifications**: Real-time notifications to candidates and interviewers are currently logged as events (`ApplicationEvent`, `AuditEvent`) rather than dispatched via external SMTP/Twilio gateways.
2. **Document Parsing**: Resume artifacts store simulated text summaries and parsed skill arrays; PDF binary OCR parsing is abstracted for synthetic reproducibility.
3. **Calendar Integration**: Interviews are scheduled in internal database tables rather than synchronized to external Google Calendar or Microsoft Outlook Exchange APIs.
