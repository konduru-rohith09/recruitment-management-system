# AI Prompt History and Human-in-the-Loop Development Log

## 1. Purpose and Accuracy Disclosure

This document describes the AI-assisted development workflow for the Recruitment Management System, including representative prompts, human review, debugging, testing, and submission preparation.

**Important disclosure:** This is a reconstructed project-specific record, not a complete verbatim export of every prompt submitted to every AI tool. The representative prompts below illustrate a structured workflow; they must not be presented as proof that all 50 prompts were used.

Where original prompts or responses are unavailable, the record should be labelled as reconstructed. Only claim that a prompt was used, a decision was made, or a test passed when the available evidence supports that claim.

## 2. Human-in-the-Loop Workflow

The intended development process follows these steps:

1. Define the requirement and constraints.
2. Ask AI for an explanation, proposal, or targeted implementation.
3. Review the response and compare it with the actual code.
4. Accept, modify, or reject the suggestion.
5. Run the relevant tests or manual checks.
6. Record the actual result and remaining limitations.

AI-generated code and explanations are suggestions, not proof of correctness. The developer remains responsible for the final implementation and its verification.

## 3. Project Evidence

The following details were recorded during project development:

- **Repository:** `konduru-rohith09/recruitment-management-system`
- **Branch:** `main`
- **Frontend:** React and Vite, deployed on Vercel.
- **Backend:** FastAPI, deployed on Render.
- **Frontend URL:** https://recruitment-management-system-three.vercel.app/
- **Backend URL:** https://recruitment-management-system-api.onrender.com
- **API documentation:** https://recruitment-management-system-api.onrender.com/docs
- **Health endpoint:** https://recruitment-management-system-api.onrender.com/health
- **Frontend API configuration:** The recorded implementation uses `VITE_API_URL` with a fallback in `frontend/src/App.jsx`.
- **Repository areas:** `src/`, `api/`, `app/`, `frontend/`, `migrations/`, and `tests/`, along with project configuration and documentation files.

### Recorded debugging evidence

During deployment troubleshooting, the following observations were recorded:

- A request to the deployed backend health endpoint returned HTTP `200 OK`.
- The health response reported `status: UP` and `database: HEALTHY`.
- A request carrying the deployed Vercel origin returned a matching `access-control-allow-origin` response header.
- Chrome displayed `net::ERR_BLOCKED_BY_CLIENT`.
- The site was subsequently reported to connect in Incognito mode.

**Conclusion supported by this evidence:** The health endpoint and the tested CORS response worked at the time of those checks. Browser-side blocking was a plausible explanation for the normal-browser failure, but the exact cause was not conclusively established.

The recorded Git history also included commits identified as `7b66eac`, `936757e`, and `43c73bd`. Confirm current commit references with `git log --oneline` before using them as evidence.

## 4. Representative Prompt History

The following 50 entries are organized into eight phases. They are **representative prompt templates**, not a claim that each prompt was submitted verbatim or used during the original development.

For an actual submission, mark each relevant entry as **Original prompt**, **Reconstructed from actual work**, or **Proposed workflow**.

### Phase 1 — Requirements and scope

#### 01. Clarify the problem

**Representative prompt:**

> Act as a senior software engineer. Help me clarify the problem, intended users, core workflows, constraints, assumptions, and acceptance criteria for a Recruitment Management System. Separate confirmed requirements from questions that need my decision. Do not invent requirements.

**Human review:** Confirm the requirements and correct assumptions that do not match the project brief.

**Validation:** Compare the approved requirements with the implemented functionality.

#### 02. Map the recruitment workflow

**Representative prompt:**

> Map the recruitment process through screening, interview scheduling, workflow tracking, offer handling, and audit logging where supported. Identify inputs, outputs, possible failures, and uncertain business rules.

**Human review:** Confirm the workflow stages and remove features outside the project scope.

**Validation:** Compare the proposed workflow with the actual source files.

#### 03. Prioritize scope

**Representative prompt:**

> Separate essential requirements from optional features. Prioritize reliable, testable functionality and explain the risks of adding optional features under a limited deadline.

**Human review:** Select the work that best satisfies the project requirements.

**Validation:** Check the implementation against the agreed scope.

#### 04. Define acceptance criteria

**Representative prompt:**

> Convert the confirmed requirements into observable acceptance criteria. Include valid inputs, invalid inputs, rejected workflow transitions, scheduling edge cases, and offer validation where applicable.

**Human review:** Ensure the criteria describe the intended application rather than assumptions.

**Validation:** Map criteria to tests or manual checks.

#### 05. Propose a repository structure

**Representative prompt:**

> Propose a maintainable Python recruitment-system structure covering models, database access, screening, scheduling, workflow, offers, audit, validation, API, frontend, migrations, and tests where relevant. Explain each component's responsibility without generating the entire application at once.

**Human review:** Evaluate the proposed module boundaries.

**Validation:** Compare the proposal with the actual repository.

### Phase 2 — Architecture and design

#### 06. Critique the architecture

**Representative prompt:**

> Review the proposed architecture for overengineering, duplicated responsibilities, circular dependencies, and unjustified features. Recommend the simplest viable design.

**Human review:** Accept only simplifications that fit the requirements.

**Validation:** Check that every retained module has a clear purpose.

#### 07. Define module interfaces

**Representative prompt:**

> For each relevant module, describe its responsibility, inputs, outputs, expected errors, and dependencies. Keep business rules separate from HTTP handlers and persistence where practical.

**Human review:** Confirm that the interfaces are understandable.

**Validation:** Compare the description with actual function signatures and imports.

#### 08. Review data models

**Representative prompt:**

> Review the supplied model requirements and propose only the entities and fields the application needs. Explain field types, required values, relationships, and validation rules.

**Human review:** Reject unnecessary fields and data collection.

**Validation:** Compare models with migrations and tests.

#### 09. Identify ambiguous business rules

**Representative prompt:**

> Identify ambiguous business rules, explain possible interpretations and their consequences, and ask for a decision instead of silently choosing an interpretation.

**Human review:** Make the decisions that require project context.

**Validation:** Confirm that code and documentation use the same rules.

#### 10. Plan testing

**Representative prompt:**

> Propose a test plan covering module behavior, integration boundaries, invalid inputs, workflow transitions, scheduling, offers, and reproducibility where applicable. Distinguish essential tests from optional tests.

**Human review:** Prioritize testing according to risk.

**Validation:** Compare the test suite with the acceptance criteria.

### Phase 3 — Implementation and business logic

#### 11. Implement one module at a time

**Representative prompt:**

> Help implement the selected module using the existing project conventions. Work only on the supplied file or function, preserve unrelated behavior, explain assumptions, and ask for missing source context rather than inventing it.

**Human review:** Inspect the proposed changes before accepting them.

**Validation:** Review the Git diff and run relevant tests.

#### 12. Improve code readability

**Representative prompt:**

> Review this implementation for naming, readability, duplication, and unnecessary complexity. Explain each proposed change and avoid altering behavior without a specific reason.

**Human review:** Keep changes that improve maintainability without adding unnecessary risk.

**Validation:** Run relevant regression tests.

#### 13. Review validation rules

**Representative prompt:**

> Identify valid inputs, invalid inputs, boundary cases, and expected outcomes for this module. Distinguish malformed input from a valid input that violates a business rule.

**Human review:** Confirm the intended validation behavior.

**Validation:** Test valid and invalid cases.

#### 14. Identify edge cases

**Representative prompt:**

> Review the supplied module for relevant edge cases, including missing values, wrong types, empty collections, duplicate identifiers, invalid dates, and unexpected states. Rank possible defects by severity.

**Human review:** Confirm which findings apply to the actual implementation.

**Validation:** Add regression tests for confirmed defects where feasible.

#### 15. Review screening logic

**Representative prompt:**

> Review candidate-screening logic against the supplied criteria. Explain how each criterion affects the outcome and how missing data is handled. Do not invent hiring criteria or use protected characteristics as screening shortcuts.

**Human review:** Confirm that screening rules match legitimate project requirements.

**Validation:** Test representative eligible, ineligible, and incomplete records.

#### 16. Review scheduling behavior

**Representative prompt:**

> Review scheduling logic for date and time validation, timezone assumptions, duplicate slots, and conflicts where supported. Distinguish confirmed defects from optional improvements.

**Human review:** Confirm the required scheduling rules.

**Validation:** Run scheduling tests and document untested behavior.

#### 17. Review workflow transitions

**Representative prompt:**

> Identify allowed and disallowed workflow transitions based on the actual requirements. Recommend explicit transition rules and clear errors for rejected transitions.

**Human review:** Confirm that the transition policy matches the intended workflow.

**Validation:** Test successful and rejected transitions.

#### 18. Review offer management

**Representative prompt:**

> Review offer handling using the states and required fields present in the requirements and code. Identify invalid transitions and missing-field cases without inventing unsupported functionality.

**Human review:** Confirm which offer behaviors are in scope.

**Validation:** Run offer tests and inspect the actual state changes.

#### 19. Review audit events

**Representative prompt:**

> Review audit-event handling. Identify meaningful state changes to record and the minimum context needed for traceability. Avoid storing credentials, tokens, or unnecessary personal information.

**Human review:** Evaluate event usefulness and privacy implications.

**Validation:** Inspect actual audit events from representative operations.

#### 20. Review reproducible data generation

**Representative prompt:**

> Review the data-generation process. Explain whether it inserts, replaces, or appends records and how deterministic inputs affect repeatability. Identify safeguards against accidental destructive changes.

**Human review:** Confirm safe behavior for development and testing.

**Validation:** Test in a safe environment and record the observed behavior.

### Phase 4 — API and frontend integration

#### 21. Compare API contracts

**Representative prompt:**

> Compare the actual API routes and request/response schemas with the frontend's expectations. Identify mismatched field names, status codes, query parameters, and error formats using the supplied source code.

**Human review:** Inspect both sides before choosing a fix.

**Validation:** Test the affected route directly and through the frontend.

#### 22. Review frontend API configuration

**Representative prompt:**

> Review the React/Vite API base URL configuration. Use `VITE_API_URL` for the deployed backend, keep local development understandable, avoid an incorrect production localhost fallback, and explain which changes require a rebuild.

**Human review:** Verify the actual configuration and deployment settings.

**Validation:** Inspect the request URL in the browser Network panel.

#### 23. Improve API error handling

**Representative prompt:**

> Review frontend API error handling. Distinguish HTTP errors, network failures, CORS rejections, browser-side request blocks, and malformed responses where the evidence allows. Do not label the backend as unavailable without supporting evidence.

**Human review:** Ensure user-facing messages reflect observed failures.

**Validation:** Inspect relevant error responses and browser behavior.

#### 24. Review loading and empty states

**Representative prompt:**

> Inspect the frontend for loading, empty, success, and error states. Identify cases where missing or stale data could be mistaken for current data.

**Human review:** Prioritize improvements that fit the project scope.

**Validation:** Manually check the states supported by the application.

#### 25. Verify request construction

**Representative prompt:**

> Trace the actual frontend API requests. Verify base URL joining, trailing slashes, query parameters, and response parsing from the source code rather than inferring behavior from filenames.

**Human review:** Compare source code with browser Network observations.

**Validation:** Confirm actual request URLs and responses.

### Phase 5 — Testing and debugging

#### 26. Plan tests before refactoring

**Representative prompt:**

> Identify the observable behavior and tests needed to preserve it before refactoring this module. Separate intended behavior from accidental behavior.

**Human review:** Decide which existing behaviors are requirements.

**Validation:** Run or add tests before changing the implementation.

#### 27. Review test quality

**Representative prompt:**

> Review these tests for meaningful assertions, isolation, deterministic data, and negative cases. Identify tests that could pass without verifying the intended behavior.

**Human review:** Preserve meaningful assertions rather than weakening them to make tests pass.

**Validation:** Run the affected tests.

#### 28. Diagnose a failing test

**Representative prompt:**

> Given the exact failing test output and relevant source code, separate the observed symptom from possible causes. Recommend the smallest evidence-supported fix and a regression test. Ask for additional evidence if the cause remains uncertain.

**Human review:** Verify that the proposed diagnosis matches the actual code and output.

**Validation:** Re-run the failing test after the fix.

#### 29. Check for regressions

**Representative prompt:**

> Review this diff for unintended changes to public interfaces, validation, database behavior, and workflow transitions. Identify which regression tests should be rerun.

**Human review:** Inspect the diff and choose the appropriate tests.

**Validation:** Record actual test results.

#### 30. Review determinism

**Representative prompt:**

> Review reproducibility tests for randomness, timestamps, iteration order, environment variables, and external services. Recommend controls only where they are appropriate.

**Human review:** Decide which sources of variability should be controlled.

**Validation:** Run the relevant tests more than once and compare results.

#### 31. Interpret test output

**Representative prompt:**

> Explain the appropriate test command for the repository and how to interpret failures, errors, and skipped tests. Do not report a test count or successful result unless the actual output supports it.

**Human review:** Run the command and inspect the result.

**Validation:** Record the command and real summary.

#### 32. Identify test coverage gaps

**Representative prompt:**

> Rank the most important untested behaviors based on confirmed requirements and risk. Distinguish a coverage gap from a confirmed bug and recommend a small set of useful additional tests.

**Human review:** Choose the next tests based on impact and available time.

**Validation:** Record which gaps were addressed and which remain.

### Phase 6 — Database, configuration, and deployment

#### 33. Review migration safety

**Representative prompt:**

> Inspect the migration configuration and scripts. Explain the schema changes, reversibility, and possible data-loss risks. Do not recommend production migrations without a confirmed target and recovery plan.

**Human review:** Verify the target environment and recovery approach.

**Validation:** Test migrations safely where possible.

#### 34. Protect secrets

**Representative prompt:**

> Review environment-variable requirements and `.env.example`. Use placeholders in documentation, confirm that the real `.env` is excluded from Git, and distinguish frontend-public configuration from backend secrets.

**Human review:** Inspect local configuration without exposing credentials.

**Validation:** Check Git tracking and example-file contents.

#### 35. Review Docker configuration

**Representative prompt:**

> Inspect the Dockerfile, dependency files, working directory, startup command, port configuration, and runtime assumptions. Suggest changes only when supported by the supplied files.

**Human review:** Determine whether Docker is part of the required setup.

**Validation:** Record actual build and startup results if tested.

#### 36. Review Render deployment

**Representative prompt:**

> Help inspect the Render backend configuration, including startup command, dependencies, port binding, environment variables, health endpoint, and logs. Distinguish code defects from hosting configuration issues.

**Human review:** Inspect actual settings and logs without sharing secret values.

**Validation:** Check the health endpoint and relevant API routes.

#### 37. Review Vercel deployment

**Representative prompt:**

> Help verify Vercel's root directory, build command, output directory, production branch, deployed commit, and `VITE_API_URL`. Explain how to confirm that the latest build is deployed.

**Human review:** Compare hosting settings with the repository.

**Validation:** Open the deployed site and inspect its requests.

#### 38. Diagnose CORS systematically

**Representative prompt:**

> Guide me through diagnosing frontend-to-backend connectivity using the browser Console, Network panel, exact origin, preflight behavior, and response headers. Distinguish CORS errors from browser-side blocks and server errors.

**Human review:** Gather evidence before changing configuration.

**Validation:** Compare the tested origin with the returned CORS header and verify the browser request.

#### 39. Interpret health checks

**Representative prompt:**

> Explain how to check the deployed health endpoint with `curl.exe` or a browser. Clarify what the HTTP status, JSON body, and response headers prove and what they do not prove.

**Human review:** Run the command and record the real response.

**Validation:** Check additional routes instead of treating health as proof of full-system functionality.

#### 40. Investigate browser-side blocking

**Representative prompt:**

> Chrome reports `ERR_BLOCKED_BY_CLIENT` for an API request. Help determine whether browser-side blocking is involved by comparing normal browsing and Incognito mode, inspecting DevTools, and checking the backend independently.

**Human review:** Compare browser behavior and investigate extensions before changing deployment settings.

**Validation:** Claim a specific cause only if a controlled test identifies it.

### Phase 7 — Documentation and engineering reasoning

#### 41. Improve the README

**Representative prompt:**

> Review the README from the perspective of a reviewer who has never seen this project. Identify missing prerequisites, installation commands, environment configuration, database setup, startup instructions, tests, and troubleshooting. Flag unverified instructions.

**Human review:** Follow the instructions and correct steps that fail.

**Validation:** Verify the setup in a clean environment where feasible.

#### 42. Explain design decisions

**Representative prompt:**

> Explain the actual architecture and important design choices. For each choice, describe the problem, chosen approach, alternative, and trade-off. Do not claim a design pattern is implemented unless the code demonstrates it.

**Human review:** Ensure that each decision can be explained in the developer's own words.

**Validation:** Connect explanations to source files or tests.

#### 43. Document limitations honestly

**Representative prompt:**

> Classify features as implemented, partially implemented, not implemented, or not tested based on the source and evidence provided. Do not describe planned work as completed work.

**Human review:** Correct statuses that overstate application capabilities.

**Validation:** Check each claim against code and results.

#### 44. Prepare reviewer verification steps

**Representative prompt:**

> Write a verification checklist using actual repository commands. Include prerequisites, setup, application startup, tests, and key behavior. State the observable expected result and identify steps that depend on external services.

**Human review:** Correct any instruction that is not reproducible.

**Validation:** Keep the checklist aligned with actual behavior.

#### 45. Review the final Git diff

**Representative prompt:**

> Review the current Git diff for secrets, generated files, unrelated edits, weakened tests, unsupported documentation claims, and accidental deployment changes. Recommend the smallest safe corrections based on the actual diff.

**Human review:** Inspect findings before accepting changes.

**Validation:** Re-run relevant tests and inspect the final diff.

### Phase 8 — Git history and submission readiness

#### 46. Prepare meaningful commits

**Representative prompt:**

> Review the actual changes and suggest accurate commit messages and logical groupings. Do not fabricate development history or create commits merely to make the history look larger.

**Human review:** Commit only genuine work.

**Validation:** Inspect `git status` and `git log --oneline`.

#### 47. Document AI use accurately

**Representative prompt:**

> Help document each real AI interaction by separating the prompt, AI contribution, human changes, and validation evidence. Mark reconstructed wording clearly and do not invent prompts or test results.

**Human review:** Compare the record with available conversation history and code changes.

**Validation:** Ensure the record does not overstate what happened.

#### 48. Prepare to explain the implementation

**Representative prompt:**

> Ask me one technical question at a time about the architecture, models, validation, scheduling, workflow, offers, persistence, tests, deployment, and limitations. Correct misunderstandings without inventing personal experience.

**Human review:** Answer in my own words and study topics I cannot explain.

**Validation:** Rehearse using the actual source code.

#### 49. Prepare a technical walkthrough

**Representative prompt:**

> Prepare a short walkthrough of the actual repository, covering the problem, architecture, representative business flow, tests, deployment, AI assistance, and known limitations. Identify the file, test, command, or live behavior that supports each claim.

**Human review:** Remove claims that cannot be demonstrated.

**Validation:** Rehearse with the current code and deployment.

#### 50. Audit submission readiness

**Representative prompt:**

> Audit the repository against the submission criteria, including executable code, reproducible setup, Git history, AI prompt history, design reasoning, test evidence, limitations, and readiness for a technical walkthrough. Mark each item verified, partially verified, or not verified using supporting evidence.

**Human review:** Identify remaining work without marking unsupported items complete.

**Validation:** Record the actual status of each criterion.

## 5. Prompt-to-Evidence Traceability

Use the following table for important AI interactions that materially affected the delivered project. Populate it only with genuine evidence. A smaller set of well-supported entries is better than fabricated evidence for every prompt.

| Prompt number | Classification | Related file or commit | Human decision or change | Validation evidence |
|---|---|---|---|---|
| [Number] | Original / reconstructed / proposed | [Actual path or commit] | [Actual decision] | [Actual test or command result] |
| [Number] | Original / reconstructed / proposed | [Actual path or commit] | [Actual decision] | [Actual test or command result] |
| [Number] | Original / reconstructed / proposed | [Actual path or commit] | [Actual decision] | [Actual test or command result] |

## 6. Human Contribution Summary

Complete these items with genuine details before submission.

- **Requirements clarified:** [Describe actual decisions.]
- **Architecture decisions made:** [Describe choices and trade-offs you can explain.]
- **Code reviewed or changed after AI assistance:** [Identify real files or examples.]
- **AI suggestions rejected or corrected:** [Give a real example, or state that none has been recorded.]
- **Tests actually run:** [Provide exact commands and real results.]
- **Deployment checks performed:** [Provide actual endpoint results and browser observations.]
- **Known limitations:** [List real gaps and unverified behavior.]

## 7. Evidence Log

| Date/time | Evidence | Actual result | Status |
|---|---|---|---|
| [Date/time] | [Test command and output] | [Observed result] | Pass / fail / not run |
| [Date/time] | [Health or API request] | [Actual status and response] | Verified for that check / failed |
| [Date/time] | [Frontend manual check] | [Observed behavior] | Verified for that check / not verified |
| [Date/time] | [Git commit or diff] | [Actual change] | Committed / not committed |

## 8. Limitations of This Record

This document does not claim to preserve every original prompt, AI response, or timestamp. Original prompt exports or notes should be added if available.

The 50 entries are representative prompt templates and must not be represented as a verbatim history of all AI interactions. They are not evidence that each interaction occurred.

No AI-generated statement should be treated as proof that a feature works unless it is supported by source-code inspection, a reproducible command, a test result, or an observed application behavior.

**Submission integrity:** Clearly distinguish original prompts from reconstructed summaries and proposed prompts. Record genuine human decisions, failed attempts, corrections, and validation results wherever evidence is available. The purpose of this document is to make AI-assisted development transparent and reviewable, not to create an artificial development history.
