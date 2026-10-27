# Design Decisions

## Recruitment Management System

This document explains the architecture, implementation choices, trade-offs, and limitations of the Recruitment Management System. It also records the evidence used to evaluate these choices.

## 1. Project Goal

The Recruitment Management System organizes recruitment activities, including candidate screening, interview scheduling, recruitment workflow tracking, offer handling, validation, audit functionality, and related reporting.

The goal is to keep recruitment responsibilities organized, make the system easier to maintain, and provide a foundation for testing and reviewing recruitment workflows.

## 2. Architecture

The repository separates the application into several areas:

- `src/` — core models and recruitment business logic, including screening, scheduling, workflow, offers, validation, and audit functionality.
- `api/` — backend API functionality.
- `app/` — application functionality, where present in the implementation.
- `frontend/` — React and Vite frontend.
- `tests/` — automated tests.
- `schemas/` — schema definitions, where used.
- `migrations/` — database migration scripts.
- `data/` and `reports/` — project data and report-related resources, where applicable.

FastAPI provides the backend API, while the frontend is deployed separately.

**Why this structure:** Separating business logic, API functionality, frontend code, and tests makes responsibilities easier to locate and maintain.

**Trade-off:** A modular structure introduces additional files and interfaces that developers must understand and maintain.

## 3. Decision: Separate Business Responsibilities

**Decision:** Keep recruitment responsibilities such as screening, scheduling, workflow transitions, offer handling, audit behavior, and validation in separate modules where supported by the implementation.

**Reasoning:** Each responsibility can be reviewed, tested, and modified with less risk of unintentionally affecting unrelated functionality.

**Alternative considered:** Place all recruitment business rules in one large application module.

**Trade-off:** Separate modules improve organization and testability but require clear interfaces between components.

**Evidence:** The repository contains corresponding recruitment modules and automated test files. The implementation and tests should be reviewed together to confirm the exact behavior of each module.

## 4. Decision: Use FastAPI for the Backend

**Decision:** Use FastAPI to expose backend functionality through HTTP endpoints.

**Reasoning:** An API separates backend operations from the user interface and provides an interface that can be inspected through interactive API documentation.

The deployed API documentation is available at:

https://recruitment-management-system-api.onrender.com/docs

The health endpoint is available at:

https://recruitment-management-system-api.onrender.com/health

**Trade-off:** An API-based architecture requires correct configuration of routes, request and response formats, error handling, and cross-origin access.

The health endpoint provides evidence only for the checks implemented by that endpoint. It does not establish that every API route works correctly.

## 5. Decision: Deploy the Frontend and Backend Separately

**Decision:** Deploy the frontend on Vercel and the backend on Render.

- Frontend: https://recruitment-management-system-three.vercel.app/
- Backend: https://recruitment-management-system-api.onrender.com

**Reasoning:** Separate deployments allow the frontend and backend to be built and deployed independently.

**Alternative considered:** Serve the frontend and backend from a single deployment.

**Trade-off:** Separate hosting makes independent deployment possible but requires correct API URL configuration, CORS settings, and environment variables.

## 6. Decision: Use Environment-Based API Configuration

**Decision:** The frontend reads `VITE_API_URL` and includes a fallback in `frontend/src/App.jsx`, according to the recorded implementation details.

**Reasoning:** This allows the frontend to target the deployed backend instead of depending on a local API URL.

**Alternative considered:** Hard-code a localhost URL into the production frontend.

**Trade-off:** Vite environment variables are embedded during the frontend build. Changing the production value generally requires rebuilding and redeploying the frontend.

Variables prefixed with `VITE_` are exposed to browser-side code. They must never contain passwords, API keys, or other secrets.

**Evidence recorded:** The deployed frontend was observed making requests to the Render health endpoint. The repository history previously identified commits `936757e` for environment-based API configuration and `43c73bd` for the deployed backend URL fallback. Verify these commit references against the current Git history before submission.

## 7. Decision: Use Database Configuration and Migrations

**Decision:** The repository includes database configuration and migration-related artifacts, including `alembic.ini`, a `migrations/` directory, and a utility for SQLite-to-MySQL conversion.

**Reasoning:** Recruitment records require persistent storage, a defined schema, and a controlled approach to schema changes.

**Alternative considered:** Keep all operational data in temporary in-memory structures or change database schemas manually without migration scripts.

**Trade-off:** Database configuration and migrations add setup and operational complexity but provide a more structured way to manage persistent data and schema changes.

The deployed health endpoint previously reported the database as `HEALTHY`. This confirms only the state reported by that endpoint at the time checked.

Before making database changes, verify the actual database configuration, inspect the migration scripts, and understand the recovery process. Do not run destructive migrations against production without a recovery plan.

## 8. Decision: Maintain Automated Tests

**Decision:** Keep automated tests in the dedicated `tests/` directory.

**Reasoning:** Automated tests help check expected behavior, detect regressions, and provide repeatable evidence that selected functionality works.

**Alternative considered:** Rely entirely on manual testing.

**Trade-off:** Tests require time to create and maintain, and passing tests do not prove the absence of defects. Manual verification is still necessary for browser behavior, deployment, and complete user workflows.

**Recorded evidence:** The documented Python test run completed with 19 tests passed and 0 failed in 11.38 seconds.

The frontend dependency installation and production build were also reported as successful in the testing documentation.

These results apply to the recorded runs and should not be treated as proof that every feature works in production.

See `TESTING.md` for the commands, recorded results, and outstanding verification gaps.

## 9. Decision: Diagnose Deployment Problems Using Evidence

**Decision:** Investigate frontend/backend connectivity using browser Console output, the Network panel, the health endpoint, and HTTP response headers before changing hosting configuration.

**Reasoning:** A failed browser request can originate from an incorrect API URL, CORS configuration, browser-side blocking, or a server-side failure. Each cause requires a different response.

**Alternative considered:** Repeatedly redeploy the backend or modify CORS configuration without first identifying the failing request.

**Trade-off:** Evidence gathering takes additional time but helps avoid unnecessary configuration changes.

**Evidence recorded:**

- A request to the deployed health endpoint returned HTTP 200.
- The response reported the application status as `UP` and database status as `HEALTHY`.
- A request carrying the Vercel frontend origin returned a matching `access-control-allow-origin` header.
- The browser Console showed `net::ERR_BLOCKED_BY_CLIENT`.
- The site was subsequently reported to connect in Incognito mode.

The browser error makes client-side blocking a possible explanation, but the exact cause was not conclusively established. A successful health request also does not prove that every API route or frontend workflow works.

## 10. Decision: Document AI Use and Human Review

**Decision:** Maintain a prompt history that distinguishes AI-assisted work, human review, and validation evidence.

**Reasoning:** Transparent documentation helps reviewers understand how AI was used and how generated suggestions were evaluated.

**Alternative considered:** Include only a general statement that AI was used.

**Trade-off:** Maintaining a detailed record takes time. Reconstructed prompt records must be identified honestly rather than presented as complete verbatim transcripts when the original prompts are unavailable.

**Evidence:** See `PROMPT_HISTORY.md` for the recorded AI-use history. Compare it with available conversation records, code changes, Git diffs, and test results before submission.

## 11. Screening and Responsible Use

Screening functionality should support informed human review rather than automatically determine hiring outcomes without appropriate oversight.

Recruitment decisions can significantly affect applicants. Screening results should therefore be reviewed for incorrect outputs, inconsistent treatment, and inappropriate use of candidate data.

Any claims about fairness checks, bias mitigation, explainability, or access controls should be supported by implemented functionality and verifiable evidence. These safeguards should not be described as complete unless they have actually been implemented and tested.

## 12. Trade-Offs and Limitations

The following limitations should be considered when evaluating the project:

- Automated tests cover only the scenarios represented in the test suite.
- A passing test suite does not guarantee the absence of defects.
- A health endpoint confirms only the checks implemented by that endpoint.
- A successful CORS header check for one origin and route does not prove that every endpoint or preflight request works.
- Local build success does not prove that the latest deployed application works correctly.
- Deployment behavior can differ from local behavior because of environment variables, hosting configuration, and browser restrictions.
- Full end-to-end verification of every recruitment workflow has not been established by the recorded evidence.
- Screening outputs require appropriate human oversight.
- Any feature not demonstrated by source code or repeatable evidence should be described as unverified, incomplete, or out of scope.

## 13. Further Improvements

Potential improvements include:

1. Expand API tests to cover success cases, invalid inputs, and error responses.
2. Add broader browser-level and end-to-end tests for recruitment workflows.
3. Strengthen validation of workflow transitions and business rules.
4. Improve logging and observability to make deployment failures easier to diagnose.
5. Review candidate-data handling, access controls, and privacy safeguards.
6. Evaluate screening behavior for inconsistent or inappropriate outcomes.
7. Add reproducible fresh-installation instructions and verify them in a clean environment.

These are potential improvements, not claims that the work has already been completed.

## 14. Questions to Prepare for Review

1. Why were screening, scheduling, workflow, and offer handling separated into modules?
2. Where are workflow transitions validated, and how are invalid transitions handled?
3. How do the automated tests verify invalid inputs and edge cases?
4. How does the frontend select the deployed backend URL?
5. What does the health endpoint prove, and what does it not prove?
6. How was a possible CORS issue distinguished from browser-side request blocking?
7. Which AI suggestions were accepted, modified, or rejected, and how were the results validated?
8. What are the current limitations, and which improvement would be prioritized next?

## 15. Evidence References

The following project artifacts can support a review of the design decisions:

- **Source code:** Review the relevant files under `src/`, `api/`, and `frontend/`.
- **Automated tests:** Review the test modules under `tests/`.
- **Testing evidence:** See `TESTING.md`.
- **AI-use documentation:** See `PROMPT_HISTORY.md`.
- **Git history:** Confirm relevant commit references using `git log --oneline`.
- **Deployment evidence:** Recheck the health endpoint and frontend deployment before submission.
- **Outstanding issues:** Record actual failures and unverified behavior rather than assuming that all checks passed.

This document describes the rationale and available evidence for the project's design. All implementation claims should remain consistent with the current repository and the results that can be reproduced.
