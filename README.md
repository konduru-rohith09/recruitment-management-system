# Recruitment Management System

A recruitment management system that helps organize the hiring process, from creating a job opening to managing interviews and making offer decisions.

I built this project to bring the main steps of recruitment into one place and make the process easier to track and validate. It focuses on practical hiring problems such as inconsistent screening, interview scheduling conflicts, missing feedback, salary mismatches, and applications that remain active after a role is closed.

The project includes a FastAPI backend, a database layer, a Streamlit analytics dashboard, and automated tests for important recruitment rules.

## Live Demo

- **Frontend:** https://recruitment-management-system-three.vercel.app/
- **Backend API:** https://recruitment-management-system-api.onrender.com
- **API Documentation:** https://recruitment-management-system-api.onrender.com/docs
- **API Health Check:** https://recruitment-management-system-api.onrender.com/health

The frontend is hosted on Vercel, while the backend API runs on Render. The frontend uses the API to access recruitment-related information and functionality.

## What Does This Project Do?

The system manages different parts of the recruitment process and checks that important rules are followed.

### 1. Job Requisition Management

Recruiters need to keep track of open positions, required headcount, and salary limits. This module manages job requisitions and supports the rules associated with opening and closing positions.

### 2. Candidate Screening

Candidates are evaluated using configurable, weighted criteria such as relevant skills, experience, and assessment results. The system is designed to make screening scores explainable instead of relying on an unexplained final score.

Screening criteria should be job-related and should not use protected or demographic characteristics such as age, gender, caste, religion, or disability.

### 3. Interview Scheduling

The scheduling module checks interviewer availability and identifies overlapping interview slots. It also prevents inactive interviewers from being assigned to interviews where the relevant business rules prohibit the assignment.

### 4. Recruitment Workflow

Applications move through defined recruitment stages. The system validates transitions and prevents certain decisions from being made before required steps are complete.

For example, an application should not advance to a pending decision when required interviewer feedback is still missing.

### 5. Offer Management

The offer module checks proposed compensation against the salary band associated with a requisition. Offers outside the approved range require the appropriate exception handling rather than being treated as ordinary offers.

### 6. Audit and Anomaly Detection

The system checks for five predefined recruitment-process anomalies:

- **Interviewer unavailable:** An interview is assigned to an inactive interviewer or conflicts with an existing booking.
- **Duplicate application:** A duplicate application attempt is identified and flagged.
- **Missing feedback:** An application is advanced without all required interviewer scorecards.
- **Salary outside band:** An offer exceeds the permitted salary range without the required authorization.
- **Closed role with active applications:** A requisition is closed or cancelled while applications remain in active stages.

These checks help identify problems that need investigation or corrective action.

### 7. Recruitment Analytics

The project includes metrics for understanding how candidates move through the recruitment process. These include screening pass rate, interview completion rate, feedback submission rate, offer acceptance rate, rejection rate, withdrawal rate, and average time to decision.

The Streamlit dashboard is intended to make these metrics and anomaly records easier to review.

## Technologies Used

| Technology | How it is used |
|---|---|
| Python | Core application logic and business rules |
| FastAPI | Backend REST API |
| SQLAlchemy | Database models and ORM operations |
| MySQL / SQLite | Data storage, depending on configuration |
| Pydantic | Request and data validation |
| Pandas and NumPy | Data processing and calculations |
| Faker | Synthetic data generation |
| Streamlit | Analytics dashboard |
| Plotly | Interactive charts |
| Alembic | Database schema migrations |
| pytest | Automated testing |
| Vercel | Frontend hosting |
| Render | Backend hosting |

## Project Structure

The code is organized by responsibility so that the API, business logic, dashboard, and tests can be maintained separately.

```text
recruitment-management-system/
├── api/              # FastAPI application and API routes
├── app/              # Streamlit analytics dashboard
├── src/              # Models, services and business logic
│   └── services/     # Requisition, application, interview and offer services
├── schemas/          # Database schema and documentation
├── migrations/       # Alembic database migrations
├── data/             # Generated datasets and anomaly ground truth
├── reports/          # Validation and reproducibility reports
├── tests/            # Automated tests
├── requirements.txt  # Python dependencies
├── Dockerfile        # Container configuration
├── alembic.ini       # Migration configuration
├── .env.example      # Example environment variables
└── README.md
```

## How to Run the Project Locally

### Prerequisites

Before starting, install:

- Python 3.11 or later
- Git
- MySQL 8 or later if you want to use MySQL locally

SQLite can be used for isolated testing where supported by the project configuration.

### Step 1: Clone the repository

```bash
git clone https://github.com/konduru-rohith09/recruitment-management-system.git
cd recruitment-management-system
```

### Step 2: Create a virtual environment

On Windows Command Prompt:

```cmd
python -m venv .venv
.venv\Scripts\activate
```

On Linux or macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the project dependencies:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Configure the environment

Create a local `.env` file from the provided example.

On Windows:

```cmd
copy .env.example .env
```

On Linux or macOS:

```bash
cp .env.example .env
```

Update the `DATABASE_URL` value in `.env` to match your local database configuration.

For example, a MySQL connection string has this format:

```ini
DATABASE_URL=mysql+pymysql://recruit_user:YOUR_PASSWORD@localhost:3306/recruitment_db?charset=utf8mb4
```

Replace the username, password, and database details with your own values. Never commit your real `.env` file or credentials to GitHub.

### Step 4: Initialize the database

If you are using MySQL, create the database and application user first. Then initialize the schema using the project's migration configuration:

```bash
alembic upgrade head
```

Alternatively, for a fresh database, you can use the supplied SQL schema:

```bash
mysql -u recruit_user -p recruitment_db < schemas/schema.sql
```

Use the initialization method appropriate for your setup and avoid applying both methods without checking the existing database state.

### Step 5: Generate sample data

The project includes a synthetic data generator that supports starter and full dataset sizes.

To generate the starter dataset:

```bash
python -m src.generate_data --seed 20261022 --scale starter --reset-db
```

To generate the full dataset:

```bash
python -m src.generate_data --seed 20261022 --scale full --reset-db
```

The documented starter dataset contains 10 requisitions, 100 candidates, 150 applications, 30 interviews, 10 offers, and five controlled anomalies.

The documented full dataset contains 100 requisitions, 2,000 candidates, 3,000 applications, 600 interviews, 150 offers, and five controlled anomalies.

The fixed seed is intended to make generated data repeatable. The `--reset-db` option should be used carefully because it resets generated database data.

### Step 6: Start the backend

From the project root, run:

```bash
uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```

Once the API is running, open:

- Swagger API documentation: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc
- Health check: http://127.0.0.1:8000/health
- Metrics: http://127.0.0.1:8000/metrics
- Anomalies: http://127.0.0.1:8000/anomalies

Swagger UI is useful for inspecting available endpoints and trying API requests.

### Step 7: Start the dashboard

Open a second terminal, activate the virtual environment, and run:

```bash
streamlit run app/dashboard.py --server.port 8501
```

The dashboard is designed to present recruitment metrics, hiring-stage information, interview feedback, and detected anomalies.

## Testing

I ran the project's automated test suite using:

```bash
python -m pytest -v
```

**Verified result: 19 tests passed in 11.38 seconds.**

The tests cover:

- Synthetic data generation
- Database models and relationships
- Offer issuance and acceptance
- Reproducibility
- Interview scheduling and conflict detection
- Screening rules and score thresholds
- Data validation and anomaly detection
- Recruitment workflow transitions

These results confirm that the tested scenarios passed in the development environment. They do not, by themselves, guarantee that every feature in the deployed application works correctly.

For additional details, see [`TESTING.md`](TESTING.md).

## Design Decisions

A few important decisions shaped the implementation:

- **Separate business logic from API routes:** This keeps recruitment rules easier to test and maintain.
- **Use explicit workflow transitions:** Applications should not advance when mandatory steps are incomplete.
- **Make screening explainable:** Weighted, job-related criteria make it easier to understand how a screening result was calculated.
- **Use deterministic synthetic data:** A fixed seed makes repeatable testing and debugging easier.
- **Validate before accepting important operations:** Scheduling, feedback, and compensation rules help prevent invalid states from being introduced.

See [`DESIGN_DECISIONS.md`](DESIGN_DECISIONS.md) for more information about the architecture, trade-offs, and limitations.

## Current Limitations

This project covers the core workflow and validation logic, but some production features are outside its current scope:

- **Email and SMS:** External notification delivery through services such as SMTP or Twilio is not implemented.
- **Resume parsing:** Production-grade PDF/OCR extraction is not implemented; the project uses synthetic summaries and parsed skill fields.
- **Calendar integration:** Interview scheduling is managed internally and is not synchronized with Google Calendar or Microsoft Outlook.
- **Deployment configuration:** Hosted and local environments may require different database, CORS, and frontend API URL settings.

## Security and Responsible Screening

Recruitment systems handle decisions that can affect people's careers. Screening should remain based on job-related criteria, and the results should be reviewed for unintended bias.

For development and demonstration, synthetic data is preferable unless real-data use has been authorized. Database credentials and other secrets should be kept out of source control, and production deployments should use appropriate access controls.

## AI-Assisted Development

AI tools can help with implementation ideas, debugging, documentation, and test design, but generated suggestions should be reviewed and validated before being treated as correct.

The accompanying [`PROMPT_HISTORY.md`](PROMPT_HISTORY.md) documents the AI-assisted workflow and human review notes. It is a reconstructed summary rather than a verbatim transcript of every prompt used.

## Project Status

The project brings together recruitment workflow management, screening, scheduling, offer controls, anomaly detection, and analytics in one application. The automated tests provide evidence for the scenarios they cover, while the documentation describes setup requirements, design choices, and known limitations.

**Start here:** [Open the live application](https://recruitment-management-system-three.vercel.app/)
