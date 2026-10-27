# Recruitment Management & Workflow Validation System

A recruitment workflow management platform designed to streamline the hiring lifecycle—from job requisition creation to offer acceptance. The system provides explainable candidate screening, interview scheduling, workflow validation, compensation controls, anomaly detection, and recruitment analytics.

## Key Features

- **Requisition Management:** Manage job openings, headcount requirements, salary bands, and approvals.
- **Explainable Candidate Screening:** Evaluate candidates using weighted, job-related skills, experience, and assessment criteria.
- **Interview Scheduling:** Detect interviewer availability conflicts and overlapping interview slots.
- **Workflow Automation:** Enforce valid recruitment lifecycle transitions and prevent advancement when mandatory feedback is missing.
- **Offer Management:** Validate compensation against approved salary bands and support authorized exceptions.
- **Audit & Anomaly Detection:** Identify five recruitment-process anomalies for investigation and corrective action.
- **Synthetic Data Generation:** Generate repeatable datasets using a fixed random seed.
- **Recruitment Analytics:** Track hiring metrics and conversion funnels through API endpoints and a Streamlit dashboard.
- **Automated Testing:** Validate core business rules, scheduling, offers, screening, data integrity, and reproducibility.

## Technology Stack

| Component | Technologies |
|---|---|
| Language | Python 3.11+ |
| Backend API | FastAPI, Uvicorn |
| Database & ORM | MySQL, SQLite, SQLAlchemy |
| Validation | Pydantic |
| Data Processing | Pandas, NumPy, Faker |
| Dashboard | Streamlit, Plotly |
| Database Migrations | Alembic |
| Testing | pytest |
| Configuration | python-dotenv |

## Project Architecture

```text
recruitment-management-system/
├── api/                 # FastAPI application and REST endpoints
├── app/                 # Streamlit analytics dashboard
├── src/                 # Core business logic and domain models
│   └── services/        # Recruitment domain services
├── schemas/             # SQL schema and database documentation
├── migrations/          # Alembic migration files
├── data/                # Generated datasets and ground truth
├── reports/             # Validation and reproducibility reports
├── tests/               # Automated test suite
├── requirements.txt
├── Dockerfile
├── alembic.ini
├── .env.example
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.11 or later
- Git
- MySQL 8+ for a local MySQL setup; SQLite may be used where supported by the project

### 1. Clone the Repository

```bash
git clone https://github.com/konduru-rohith09/recruitment-management-system.git
cd recruitment-management-system
```

### 2. Create a Virtual Environment

**Windows Command Prompt:**

```cmd
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**Linux/macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create your local environment file.

**Windows:**

```cmd
copy .env.example .env
```

**Linux/macOS:**

```bash
cp .env.example .env
```

Configure `DATABASE_URL` in `.env` according to your database setup. Example MySQL configuration:

```ini
DATABASE_URL=mysql+pymysql://recruit_user:YOUR_PASSWORD@localhost:3306/recruitment_db?charset=utf8mb4
```

Use the database configuration supported by your environment. Never commit real credentials, API keys, or your `.env` file to GitHub.

### 4. Initialize the Database

If using MySQL, create the database and application user first. Then initialize the schema using the migration configuration:

```bash
alembic upgrade head
```

Alternatively, the supplied SQL schema can be used for a fresh database:

```bash
mysql -u recruit_user -p recruitment_db < schemas/schema.sql
```

Use one initialization method at a time and verify the database configuration before running the application.

## Generate Synthetic Data

The data generator supports starter and full datasets using a deterministic seed.

**Starter dataset:**

```bash
python -m src.generate_data --seed 20261022 --scale starter --reset-db
```

**Full dataset:**

```bash
python -m src.generate_data --seed 20261022 --scale full --reset-db
```

The documented starter dataset contains 10 requisitions, 100 candidates, 150 applications, 30 interviews, 10 offers, and five controlled anomalies.

The documented full dataset contains 100 requisitions, 2,000 candidates, 3,000 applications, 600 interviews, 150 offers, and five controlled anomalies.

Generated outputs are configured to be exported under `data/generated/` and `data/ground_truth/`. **Use `--reset-db` carefully**, as it resets generated database data.

## Run the Application

### Start the FastAPI Backend

```bash
uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```

Available local endpoints:

- Swagger API documentation: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc
- Health check: http://127.0.0.1:8000/health
- Recruitment metrics: http://127.0.0.1:8000/metrics
- Anomaly detection: http://127.0.0.1:8000/anomalies

### Start the Streamlit Dashboard

Open a second terminal, activate the virtual environment, and run:

```bash
streamlit run app/dashboard.py --server.port 8501
```

The dashboard is designed to display recruitment KPIs, hiring-stage funnels, interview and feedback summaries, anomaly records, and validation results.

## Business Rules & Anomaly Detection

| Anomaly | Expected System Behavior |
|---|---|
| `INTERVIEWER_UNAVAILABLE` | Block an assignment when an interviewer is inactive or has an overlapping interview |
| `DUPLICATE_APPLICATION` | Flag duplicate application attempts |
| `MISSING_FEEDBACK` | Prevent workflow advancement until required interview scorecards are submitted |
| `SALARY_OUTSIDE_BAND` | Block an out-of-band offer or require an authorized exception |
| `CLOSED_ROLE_ACTIVE_APPLICATIONS` | Flag closed or cancelled requisitions that still have active applications |

These controls improve traceability and help identify recruitment-process exceptions for review.

## Recruitment Metrics

The system defines metrics for monitoring hiring performance, including:

- Screening pass rate
- Average screening score
- Interview completion rate
- Interviewer feedback submission rate
- Offer acceptance rate
- Application rejection rate
- Application withdrawal rate
- Average time to decision

Metric calculations include safeguards for empty denominators, covered by the automated tests.

## Testing

Run the automated tests from the repository root:

```bash
python -m pytest -v
```

**Verified test result:** 19 tests passed in 11.38 seconds in the development environment.

The test suite covers data generation, database models, offer management, deterministic reproducibility, interview scheduling, screening rules, data validation, and workflow transitions.

See [`TESTING.md`](TESTING.md) for detailed test instructions and verification notes.

## Documentation

- [`TESTING.md`](TESTING.md) — Testing instructions, results, and verification notes.
- [`DESIGN_DECISIONS.md`](DESIGN_DECISIONS.md) — Architecture, technical decisions, trade-offs, and limitations.
- [`PROMPT_HISTORY.md`](PROMPT_HISTORY.md) — AI-assisted development workflow, prompt examples, and human review notes. This is a reconstructed summary, not a verbatim transcript of every prompt used.

## Known Limitations

- **Notifications:** External email and SMS delivery integrations are not implemented.
- **Resume parsing:** Production-grade PDF/OCR resume extraction is not implemented; synthetic summaries and parsed skill fields are used.
- **Calendar integration:** Scheduling is managed internally and is not synchronized with Google Calendar or Microsoft Outlook.
- **Deployment configuration:** Hosted environments may require separate database, CORS, and frontend API URL configuration.

## Security & Responsible Screening

- Keep secrets and credentials out of source control.
- Use synthetic data for demonstrations unless real-data use is authorized.
- Keep screening criteria job-related and explainable, and review them for unintended bias.
- Apply appropriate database permissions and review audit records.

## Project Status

This project demonstrates recruitment workflow orchestration, validation, deterministic synthetic data generation, API development, and analytics. Refer to the test and design documentation for the evidence collected, implementation decisions, and known verification gaps.
