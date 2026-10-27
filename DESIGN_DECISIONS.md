<<<<<<< HEAD
# Design Decisions

## Recruitment Management System

This document records the reasoning behind the system's architecture and implementation. It is intended to help reviewers understand not only what the project does, but why particular choices were made.

> **Accuracy note:** This draft is based on the repository structure and deployment details currently known. Confirm each statement against the code before submission. Remove any design choice that is not implemented, and add alternatives or trade-offs that reflect the decisions you actually made.

## 1. Architecture at a glance

The repository separates the application into several areas:

- `frontend/` — React/Vite frontend.
- `api/` — API-facing code.
- `src/` — core recruitment modules, including screening, scheduling, workflow, offers, audit, validation, and supporting code where present.
- `schemas/` — schema definitions where used.
- `migrations/` — database migration scripts.
- `tests/` — automated tests.
- `data/` and `reports/` — project data and report artifacts where applicable.

The backend is deployed on Render, and the frontend is deployed on Vercel. The health endpoint has returned `HTTP 200 OK` with a response indicating that the service is up and the database is healthy during a recorded check.

## 2. Decision: separate business responsibilities into modules

**Decision:** Keep recruitment responsibilities such as screening, scheduling, workflow transitions, offer handling, audit behavior, and validation in separate modules where supported by the implementation.

**Why:** Each responsibility can be understood, tested, and changed with less risk of affecting unrelated logic.

**Alternative considered:** Put all business rules in one large application module.

**Trade-off:** A modular design introduces more files and interfaces to maintain, but improves readability and allows focused tests.

**Evidence to verify:** Review the actual module files and the corresponding tests in `tests/`.

## 3. Decision: keep automated tests alongside the implementation

**Decision:** Maintain a dedicated `tests/` directory for automated checks.

**Why:** Reviewers can inspect expected behavior independently of the UI and repeat checks after code changes.

**Alternative considered:** Rely entirely on manual testing.

**Trade-off:** Automated tests take time to write and maintain, and passing tests do not prove every possible behavior. Manual checks are still needed for deployment and browser integration.

**Evidence to verify:** Run the test suite and record the exact command, result summary, and any failures or skips in `TESTING.md`.

## 4. Decision: use environment-based frontend API configuration

**Decision:** The frontend reads `VITE_API_URL` and has a fallback in `frontend/src/App.jsx`.

**Why:** The frontend can target a deployed API rather than assuming the API is running on the developer's local machine.

**Alternative considered:** Hard-code a localhost URL into production frontend code.

**Trade-off:** Vite environment variables are embedded during the build, so a changed production value requires a new frontend build/deployment. Any variable prefixed with `VITE_` is exposed to browser-side code and must not contain secrets.

**Evidence observed:** The deployed frontend made requests to `https://recruitment-management-system-api.onrender.com/health`. The repository history includes commit `936757e` for environment-based API configuration and commit `43c73bd` for the deployed backend URL fallback.

## 5. Decision: validate deployment problems with evidence

**Decision:** Diagnose frontend/backend connectivity using the browser Console, Network panel, health endpoint, and HTTP response headers before repeatedly changing hosting configuration.

**Why:** A browser fetch failure can be caused by several layers, including an incorrect URL, CORS, a browser extension, or a server failure. These causes require different fixes.

**Alternative considered:** Repeatedly redeploying or changing CORS configuration without isolating the cause.

**Trade-off:** Evidence gathering takes a few extra steps, but reduces unnecessary configuration changes and makes the final explanation more defensible.

**Evidence observed:** A `curl.exe` request to the deployed health endpoint returned `HTTP 200 OK`, `status: UP`, and `database: HEALTHY`. A request carrying the Vercel origin returned an `access-control-allow-origin` header matching that origin. Chrome also showed `net::ERR_BLOCKED_BY_CLIENT`, and the site reportedly connected in Incognito. This supports investigating browser-side blocking, but does not identify a particular extension unless it was isolated experimentally.

## 6. Decision: use a relational database and migrations

**Decision:** The repository includes database configuration and migration artifacts, including `alembic.ini`, `migrations/`, and a migration utility for SQLite-to-MySQL conversion. The deployed health response reported the database as healthy at the time of the check.

**Why:** Persistent recruitment records need a defined schema and a controlled way to evolve it.

**Alternative considered:** Store all operational data only in transient in-memory structures or manually modify the schema without migration scripts.

**Trade-off:** Relational persistence and migrations add configuration and operational work, but support durable data and traceable schema changes.

**Evidence to verify:** Confirm the actual database engine and ORM configuration in code, inspect the migration scripts, and document migration testing and rollback limitations. Do not run destructive migrations against production without a recovery plan.

## 7. Decision: document AI use and human review separately

**Decision:** Maintain a prompt history that distinguishes the prompt, AI contribution, human review, and validation evidence.

**Why:** The assessment explicitly asks for transparent LLM use and visible reasoning. A useful record should show how the developer evaluated suggestions rather than treating generated output as automatically correct.

**Alternative considered:** Include only a generic statement such as “AI was used.”

**Trade-off:** A detailed log takes time to maintain and must not be presented as a verbatim transcript if prompts were reconstructed. Accuracy is more important than making the log appear perfect.

**Evidence to verify:** Compare entries with available conversation history, actual code changes, Git diffs, and test output. Label reconstructed entries honestly.

## 8. Trade-offs and limitations to discuss

Confirm which of these apply before submission:

- Automated tests cover only the cases represented in the test suite; passing tests do not guarantee absence of defects.
- A health endpoint confirms the specific checks it performs, not every API route or frontend interaction.
- A successful CORS header check for one origin and route does not prove all requests and preflight cases work.
- Deployment behavior can differ from local behavior because of environment variables, hosting configuration, and browser restrictions.
- Any feature not demonstrated by source code or repeatable evidence should be described as unverified, incomplete, or out of scope.

## 9. Questions I should be ready to answer

1. Why were screening, scheduling, workflow, and offer handling separated?
2. Which workflow transition is allowed or rejected, and where is that rule implemented?
3. How do the tests verify invalid inputs and edge cases?
4. How does the frontend select the deployed API URL?
5. What does the health endpoint prove, and what does it not prove?
6. How did I distinguish a CORS issue from a browser-side request block?
7. Which AI suggestions did I accept, modify, or reject, and how did I validate the result?
8. What are the current limitations and the next improvement I would make?

## 10. Evidence references

Fill in these references after checking the repository and running the relevant commands:

- **Source files:** [Add exact file paths for the decisions above.]
- **Tests:** [Add exact test names and real results.]
- **Git history:** `7b66eac`, `936757e`, `43c73bd` (confirm with `git log --oneline`).
- **Deployment check:** [Add date/time, endpoint, HTTP status, and sanitized output.]
- **Outstanding issues:** [List real failures, gaps, or unverified behavior.]
=======
\# Design Decisions



\## 1. Project Goal



The Recruitment Management System organizes recruitment activities, including requisitions, candidate screening, interview scheduling, workflow tracking, offers, audit checks, and reporting.



\## 2. Architecture



The project separates application responsibilities into several areas:



\- `src/`: core models, business logic, workflow, scheduling, screening, offers, validation, and audit functionality.

\- `api/`: backend API functionality.

\- `app/`: user-facing application functionality.

\- `frontend/`: frontend application.

\- `tests/`: automated tests.

\- `schemas/`: data schemas.

\- `migrations/`: database migration files.

\- `data/` and `reports/`: data and report-related project resources.



This separation helps keep core business logic distinct from the interface and API.



\## 3. Backend and API



FastAPI provides the HTTP API and interactive API documentation. The health endpoint provides a basic way to check application and database availability.



The deployed API documentation is available at:



https://recruitment-management-system-api.onrender.com/docs



\## 4. Frontend and Deployment



The frontend is built using Vite and is deployed separately from the backend.



\- Frontend: https://recruitment-management-system-three.vercel.app/

\- Backend: https://recruitment-management-system-api.onrender.com



Separating frontend and backend deployment allows each component to be built and deployed independently. It also requires correct API URL configuration and cross-origin request settings.



\## 5. Configuration and Secrets



Environment-specific configuration is supplied through environment variables. `.env.example` provides a template for local setup, while the actual `.env` file is excluded from Git.



Never commit real database passwords, API keys, access tokens, or production credentials.



\## 6. Testing Strategy



Automated Python tests validate selected application behavior. The recorded test run completed with 19 passing tests and no failures.



The frontend is checked through a clean npm installation and a production build. These checks verify installation and compilation, but do not by themselves prove that every browser workflow works correctly.



\## 7. Screening and Responsible Use



Screening outputs should support human review rather than act as the sole basis for hiring decisions. Recruitment decisions can affect applicants significantly, so the system should be reviewed for incorrect results, inconsistent treatment, and inappropriate use of candidate data.



\## 8. Limitations



\- The recorded automated test results cover only the tests that were run.

\- Full end-to-end coverage of every recruitment workflow has not been established by the evidence recorded here.

\- Deployment availability and external service behavior can change.

\- Screening results require appropriate human oversight.



\## 9. Further Improvements



Potential improvements include broader API and browser-level tests, stronger validation of workflow transitions, improved observability, and additional safeguards for candidate data and screening decisions.
>>>>>>> fd555ee (docs: prepare recruitment system submission)
