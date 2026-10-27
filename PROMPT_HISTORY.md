<<<<<<< HEAD
# Recruitment Management System — AI Prompt Engineering & Human-in-the-Loop Log

## Important accuracy note

This document is a **reconstructed, project-specific prompt-engineering workflow**, not a verbatim transcript proving that every prompt below was used. It shows how a developer can collaborate with an LLM in 50 iterative steps while retaining human control. Before submission, replace any prompt that does not match your actual work, use original wording where available, and fill in the real commands, decisions, and results. Do not claim that a prompt was used or a test passed unless that is true.

## How the workflow works

Each interaction follows a human-in-the-loop pattern:

1. **Human defines the goal and constraints.**
2. **AI proposes an approach or implementation.**
3. **Human inspects the proposal and chooses what to accept, reject, or change.**
4. **AI is asked to refine a specific issue using the available evidence.**
5. **Human runs the code/tests and checks the actual outcome.**
6. **The next prompt is based on that outcome, not on an assumption that the previous answer was correct.**

The prompts below are written as an iterative workflow for this repository. The “Human action” and “Validation” sections must be edited to reflect what actually happened.


## Concrete project evidence already observed

The following items are grounded in the project work discussed during this conversation. They are examples of evidence to connect to relevant prompts—not proof that every reconstructed prompt below was used.

- **Repository:** `konduru-rohith09/recruitment-management-system`, branch `main`.
- **Observed commit history:** `7b66eac` (initial commit), `936757e` (frontend API URL environment configuration), `43c73bd` (deployed backend URL fallback). These are genuine commits shown by `git log`.
- **Frontend configuration:** `frontend/src/App.jsx` uses `VITE_API_URL` and a fallback. The frontend is deployed on Vercel.
- **Backend:** FastAPI deployed on Render at `https://recruitment-management-system-api.onrender.com`.
- **Observed health response:** `curl.exe` returned HTTP `200 OK` and JSON reporting `status: UP` and `database: HEALTHY`.
- **Observed CORS evidence:** a request with origin `https://recruitment-management-system-three.vercel.app` returned `access-control-allow-origin` with that same origin.
- **Observed browser diagnosis:** Chrome showed `net::ERR_BLOCKED_BY_CLIENT`; the site worked in Incognito. This supports investigating browser-side blocking, but it does not by itself prove which extension caused it.
- **Repository files observed locally:** `README.md`, `requirements.txt`, `Dockerfile`, `src/`, `api/`, `app/`, `frontend/`, `migrations/`, and a `tests/` directory containing test files for generation, models, offers, reproducibility, scheduling, screening, validation, and workflow.
- **Not yet established by the evidence above:** that all tests pass now, that a clean-machine setup has been completed, or that every prompt in this document was used during original development.

### Example of evidence-based human-in-the-loop debugging

**Observed symptom:** the deployed frontend reported an API connection failure.

**Evidence collected:** the frontend was using the deployed Render URL; the health endpoint returned HTTP 200; the CORS header allowed the exact Vercel origin; Chrome showed `ERR_BLOCKED_BY_CLIENT`; the site connected in Incognito.

**Human decision:** do not keep changing backend CORS or redeploying without evidence. Compare browser contexts and inspect extensions/network errors first.

**Conclusion supported by evidence:** the backend health endpoint and the tested CORS origin were responding correctly at the time of the check. Browser-side blocking was a plausible explanation for the normal-window failure. The exact blocking extension should not be claimed as identified unless it was isolated in a controlled test.

This kind of short evidence trail is more persuasive than a generic statement that “AI fixed the bug.” Add similar evidence trails for other important changes only when you have the actual command output, code diff, or test result.

---

## Phase 1 — Define the problem and constrain the solution

### 01. Start with the problem, not code
**Prompt**
> Act as a senior software engineer. I am building a Recruitment Management System. Before suggesting code, help me clarify the problem, intended users, core workflows, constraints, assumptions, and acceptance criteria. Separate facts I have provided from questions that need my decision. Do not invent requirements.

**Human-in-the-loop:** I decide which requirements actually belong in the project and correct any assumptions that do not match the assignment.

**Next action:** Approve the requirements before moving to architecture.

### 02. Convert the requirements into a workflow
**Prompt**
> Using only the requirements we confirmed, map the recruitment process from application intake through screening, scheduling, workflow updates, offer handling, and audit logging where supported. For each stage, show inputs, outputs, possible failures, and the next allowed action. Mark uncertain business rules for my decision.

**Human-in-the-loop:** I confirm the stages and remove steps that are outside the project scope.

**Validation:** Compare the workflow with the implemented modules and README.

### 03. Define what is out of scope
**Prompt**
> Review the proposed scope and identify features that are essential versus optional. Prioritize a reliable, testable implementation over extra features. Explain the risks of adding each optional feature under a limited deadline. Do not implement anything yet.

**Human-in-the-loop:** I choose the smallest scope that satisfies the project brief and defer nonessential features.

**Validation:** Confirm the final scope is reflected in the code and documentation.

### 04. Create testable acceptance criteria
**Prompt**
> Turn the approved requirements into observable acceptance criteria. Include success cases, invalid inputs, rejected state transitions, scheduling edge cases, and offer validation where applicable. Each criterion must state what a reviewer can observe. Do not use vague wording such as “works properly.”

**Human-in-the-loop:** I review the criteria and ensure they describe the intended system rather than AI assumptions.

**Validation:** Map each criterion to a test or a manual check.

### 05. Ask for an architecture proposal, not a full application dump
**Prompt**
> Propose a maintainable repository structure for this Python Recruitment Management System. Consider models, database access, data generation, screening, scheduling, workflow, offers, audit, validation, API, frontend, migrations, and tests where relevant. Explain responsibilities and dependency direction. Do not generate all files at once.

**Human-in-the-loop:** I select the module boundaries and ask follow-up questions before implementation.

**Validation:** Compare the proposal with the actual repository structure.

---

## Phase 2 — Challenge and refine the design

### 06. Ask AI to critique its own proposal
**Prompt**
> Critically review the architecture you just proposed. Identify possible overengineering, duplicated responsibilities, circular imports, and features that are not justified by the requirements. Give me the simplest viable design and explain what you removed.

**Human-in-the-loop:** I do not accept the proposal just because it sounds sophisticated; I decide which simplifications make sense.

**Validation:** Ensure each retained module has a clear purpose.

### 07. Define module contracts
**Prompt**
> For each approved module, specify its responsibility, inputs, outputs, expected errors, and dependencies. Keep business rules separate from HTTP handlers and persistence where practical. Show one example call flow without writing implementation code yet.

**Human-in-the-loop:** I check that each module has a focused responsibility and that the interfaces are understandable.

**Validation:** Use the contracts to review function signatures and imports.

### 08. Design models from actual requirements
**Prompt**
> Inspect the model requirements I provide and propose only the entities and fields needed for this application. For each field, explain its type, whether it is required, and any validation rule. Do not add conventional HR fields unless the requirements justify them.

**Human-in-the-loop:** I approve fields and relationships and reject unnecessary data collection.

**Validation:** Compare the model definitions with migrations and tests.

### 09. Identify ambiguous rules before implementation
**Prompt**
> List any business rules that remain ambiguous in the model or workflow design. For each one, give the possible interpretations and the consequence of choosing each. Ask me to choose rather than silently selecting a rule.

**Human-in-the-loop:** I make the product decisions that require context and record the chosen interpretation.

**Validation:** Ensure code and documentation use the same interpretation.

### 10. Plan the test strategy early
**Prompt**
> Based on the approved requirements and module contracts, propose a test plan covering unit behavior, integration boundaries, invalid data, workflow transitions, scheduling, offers, and reproducibility where applicable. Distinguish required tests from optional tests and explain why each high-priority test matters.

**Human-in-the-loop:** I prioritize tests based on risk and deadline, not merely the number of tests.

**Validation:** Check that the actual test suite covers the most important acceptance criteria.

---

## Phase 3 — Implement in small, reviewable units

### 11. Ask for one module at a time
**Prompt**
> Help implement the first selected module using the existing project conventions. Work only on the file or function I provide. Explain the design briefly, preserve unrelated behavior, and list assumptions. If required source context is missing, ask me for it instead of inventing the existing code.

**Human-in-the-loop:** I provide the real source, review the patch, and decide whether it fits the architecture.

**Validation:** Inspect the diff before accepting the implementation.

### 12. Ask for a readable implementation
**Prompt**
> Review this proposed implementation for readability, naming, duplication, and unnecessary complexity. Prefer clear code over clever abstractions. Explain each recommended change and avoid changing behavior unless you identify a specific reason.

**Human-in-the-loop:** I compare the suggested refactor with the original and keep changes that improve maintainability without adding risk.

**Validation:** Re-run relevant tests after accepted changes.

### 13. Implement validation explicitly
**Prompt**
> For this module, list the valid inputs, invalid inputs, boundary cases, and expected outcomes. Then suggest validation code that follows the project's existing conventions. Distinguish malformed input from a valid input that violates a business rule.

**Human-in-the-loop:** I confirm the rules before coding and reject validation that changes the intended business behavior.

**Validation:** Test valid and invalid cases.

### 14. Ask for edge cases before calling a module complete
**Prompt**
> Do not rewrite the module yet. Review it for edge cases such as missing values, wrong types, empty collections, duplicate identifiers, invalid dates, and unexpected states where relevant. Rank findings by severity and show a minimal example for each likely defect.

**Human-in-the-loop:** I decide which findings apply to the actual feature and request a fix only for confirmed issues.

**Validation:** Add a regression test for each confirmed bug where feasible.

### 15. Keep screening rules explainable
**Prompt**
> Review the candidate-screening logic against the exact criteria I provide. For each criterion, show how the input affects the outcome and what happens if the data is missing. Do not invent hiring criteria or use protected personal characteristics as screening shortcuts.

**Human-in-the-loop:** I verify that the criteria are legitimate project requirements and that outcomes are understandable.

**Validation:** Test representative eligible, ineligible, and incomplete records.

### 16. Make scheduling assumptions explicit
**Prompt**
> Review the scheduling code for date/time validation, timezone assumptions, duplicate slots, and conflicts if those features are supported. Separate confirmed defects from optional enhancements. Do not claim concurrent booking safety without evidence from the implementation.

**Human-in-the-loop:** I decide which scheduling rules are required and which need further implementation.

**Validation:** Run the scheduling tests and record any untested concurrency behavior as a limitation.

### 17. Centralize workflow transition rules
**Prompt**
> Review the workflow state transitions. Identify the allowed and disallowed transitions based on the requirements. Recommend a single explicit transition policy and clear errors for rejected transitions. Preserve current public interfaces unless a change is necessary.

**Human-in-the-loop:** I approve the state diagram and verify that it matches the intended business process.

**Validation:** Test both successful and rejected transitions.

### 18. Keep offer rules aligned with scope
**Prompt**
> Review offer management using only the states and required fields present in the requirements and code. Identify invalid transitions and missing-field cases. Do not add approval, acceptance, or expiration behavior unless the project actually supports it.

**Human-in-the-loop:** I decide which offer behaviors are in scope and document unsupported ones.

**Validation:** Run offer tests and inspect actual state changes.

### 19. Review audit data for usefulness and privacy
**Prompt**
> Review the audit-event design. Identify which meaningful state changes should be recorded and what minimal context is needed to understand them later. Avoid storing credentials, tokens, or unnecessary personal data. Distinguish implemented audit events from recommended future work.

**Human-in-the-loop:** I select useful events and check the privacy implications of logged fields.

**Validation:** Inspect actual events from representative operations.

### 20. Make data generation reproducible
**Prompt**
> Review the project's data-generation process. Explain whether it inserts, replaces, or appends records, and identify how a seed or deterministic input affects repeatability. Recommend safeguards against accidental destructive changes. Do not claim reproducibility until it is tested.

**Human-in-the-loop:** I choose safe behavior for local development and ensure production data is not accidentally overwritten.

**Validation:** Run the generator in a safe test environment and record what happens.

---

## Phase 4 — Connect the backend and frontend

### 21. Check the API contract
**Prompt**
> Compare the actual API routes and request/response schemas with the frontend's expectations. Identify mismatched field names, status codes, query parameters, pagination, and error formats. Cite the relevant source locations and propose the smallest correction.

**Human-in-the-loop:** I inspect both sides and choose a fix based on the actual contract.

**Validation:** Test the affected route directly and through the frontend.

### 22. Make frontend configuration environment-aware
**Prompt**
> Review the React/Vite API base URL configuration. Use `VITE_API_URL` for the deployed backend, keep local development understandable, and avoid a production fallback to localhost. Explain which changes require a new Vite build. Do not expose backend-only secrets through `VITE_` variables.

**Human-in-the-loop:** I update the configuration and verify the environment variable in the hosting dashboard.

**Validation:** Inspect the deployed request URL in the browser Network panel.

### 23. Handle API errors without guessing
**Prompt**
> Review the frontend's API error handling. Distinguish HTTP errors from network failures, CORS rejections, browser-extension blocks, and malformed responses where evidence allows. Avoid telling users that the backend is down unless the available evidence supports that conclusion.

**Human-in-the-loop:** I compare messages with real failures and remove misleading diagnoses.

**Validation:** Trigger or simulate failure cases and inspect the displayed result.

### 24. Verify loading and empty states
**Prompt**
> Inspect the dashboard and list components for loading, empty, success, and error states. Identify cases where stale or missing data could be mistaken for current data. Suggest focused changes without redesigning unrelated UI.

**Human-in-the-loop:** I decide which UX changes matter for the assignment.

**Validation:** Manually check the states supported by the current application.

### 25. Check URL construction and query parameters
**Prompt**
> Trace the frontend requests for health, metrics, anomalies, and application lists in the current source. Verify base URL joining, trailing slashes, query parameters, and response parsing. Do not infer the request from a filename; show the actual code path.

**Human-in-the-loop:** I compare the source with requests visible in DevTools.

**Validation:** Confirm the final URLs and returned responses.

---

## Phase 5 — Use tests to drive correction

### 26. Ask for test cases before a large refactor
**Prompt**
> Before suggesting a refactor of this module, identify its current observable behavior and the tests needed to preserve it. Separate intended behavior from accidental behavior. Do not change implementation yet.

**Human-in-the-loop:** I decide which current behaviors are requirements and which are known defects.

**Validation:** Add or run tests before refactoring.

### 27. Review assertions, not just test execution
**Prompt**
> Review these tests for meaningful assertions, isolation, deterministic data, and negative cases. Identify tests that can pass without verifying the intended behavior. Suggest targeted improvements and do not weaken assertions merely to make the suite pass.

**Human-in-the-loop:** I inspect each suggested test and preserve checks that protect real requirements.

**Validation:** Run the relevant tests and record actual output.

### 28. Turn a failing test into a diagnosis
**Prompt**
> Here is the exact failing test output and relevant source. Separate the observed symptom, possible causes, and the cause supported by evidence. Suggest the smallest fix and one regression test. If the evidence is insufficient, tell me what to inspect next rather than guessing.

**Human-in-the-loop:** I provide real logs, inspect the proposed cause, and decide whether the patch is justified.

**Validation:** Confirm the test fails before the fix when feasible and passes after the fix.

### 29. Check for regressions
**Prompt**
> Review this diff for unintended changes to existing behavior. Identify which tests should be rerun and why. Pay particular attention to public interfaces, validation, database behavior, and workflow state transitions. Do not assume a change is safe just because the targeted test passes.

**Human-in-the-loop:** I inspect the diff and run the selected regression tests.

**Validation:** Record the actual test summary, including failures and skips.

### 30. Check determinism
**Prompt**
> Review the reproducibility tests and identify possible nondeterminism from randomness, timestamps, iteration order, environment variables, or external services. Recommend specific controls only where appropriate and do not hide real variability by weakening assertions.

**Human-in-the-loop:** I decide which variability should be controlled and which should be documented.

**Validation:** Run relevant tests more than once and compare outcomes.

### 31. Run tests and interpret evidence
**Prompt**
> Based on the repository's actual test setup, give me the appropriate command to run the suite in my active environment. Explain how to interpret failures, errors, and skipped tests. Do not report a test count or success result unless it appears in the command output I provide.

**Human-in-the-loop:** I run the command locally and share only the non-sensitive result summary.

**Validation:** Record the real command and output.

### 32. Prioritize uncovered tests
**Prompt**
> Given the current tests and confirmed requirements, rank the most important uncovered behaviors by impact and likelihood. Distinguish a coverage gap from a confirmed bug. Recommend a small next set of tests that improves confidence without adding tests for unsupported features.

**Human-in-the-loop:** I select the next tests based on risk and available time.

**Validation:** Track which tests were added and which gaps remain.

---

## Phase 6 — Database, configuration, and deployment

### 33. Review migration safety
**Prompt**
> Inspect the actual migration configuration and scripts. Explain what schema changes they make, whether they are reversible, and which operations could lose data. Do not recommend running a production migration without confirming the target environment and recovery plan.

**Human-in-the-loop:** I review the target database and avoid running risky changes without a backup/recovery plan.

**Validation:** Test migrations in a safe environment where possible.

### 34. Protect configuration secrets
**Prompt**
> Review the required environment variables and `.env.example`. Use placeholder values only in documentation, confirm the real `.env` is ignored by Git, and distinguish frontend-public configuration from backend secrets. Never ask me to paste credentials or print secret values.

**Human-in-the-loop:** I inspect configuration locally without sharing secret contents.

**Validation:** Check Git tracking and example-file contents.

### 35. Verify container setup
**Prompt**
> Inspect the Dockerfile, dependency files, working directory, startup command, port configuration, and runtime assumptions. Suggest only changes supported by the files. Provide commands to build and run locally and describe what observable result confirms startup.

**Human-in-the-loop:** I decide whether Docker is part of the required reviewer workflow and run the build if available.

**Validation:** Record whether the image build and container run were actually successful.

### 36. Verify backend hosting
**Prompt**
> Help me inspect the Render backend configuration: start command, dependencies, port binding, environment variables, health endpoint, and logs. Separate code defects from hosting configuration issues and do not ask for secret values.

**Human-in-the-loop:** I inspect the real settings and logs and apply only evidence-supported changes.

**Validation:** Check the deployed health endpoint and one or more real API routes.

### 37. Verify frontend hosting
**Prompt**
> Help me verify Vercel's root directory, build command, output directory, production branch, deployed commit, and `VITE_API_URL`. Explain which changes require a frontend redeployment and how to confirm the deployed build.

**Human-in-the-loop:** I compare Vercel's actual settings and deployment commit with the repository.

**Validation:** Open the deployed site and inspect the browser's request URL.

### 38. Diagnose CORS systematically
**Prompt**
> The deployed frontend cannot fetch from the deployed FastAPI backend. Guide me one step at a time through the browser Console, Network request, exact origin, preflight behavior, and backend response headers. Distinguish CORS from extension blocks and server errors. Do not recommend changing configuration until the evidence supports it.

**Human-in-the-loop:** I run the proposed diagnostic command and report the real output before making another change.

**Validation:** Compare the tested origin with the returned `access-control-allow-origin` header and test the actual browser request.

### 39. Interpret a health check correctly
**Prompt**
> Explain how to use `curl.exe` or a browser to check the deployed health endpoint. Tell me what HTTP status, JSON body, and response headers mean, and what a successful health check does not prove about other routes or frontend behavior.

**Human-in-the-loop:** I run the command and record its actual result.

**Validation:** Test additional routes rather than treating health alone as full-system proof.

### 40. Investigate a browser-only block
**Prompt**
> Chrome reports `ERR_BLOCKED_BY_CLIENT` for an API request. Help me test whether an extension or privacy filter is involved by comparing normal browsing and Incognito, inspecting DevTools, and checking the backend independently. Explain what each result proves and what remains uncertain.

**Human-in-the-loop:** I compare normal Chrome with Incognito and test one extension at a time instead of changing deployment settings at random.

**Validation:** Record the actual browser behavior and the cause only if the evidence identifies it.

---

## Phase 7 — Documentation and engineering reasoning

### 41. Improve the setup guide
**Prompt**
> Review the existing README from the perspective of a reviewer who has never seen this project. Identify missing prerequisites, installation commands, environment configuration, database setup, startup instructions, tests, and troubleshooting. Use commands supported by the actual repository and flag unverified instructions.

**Human-in-the-loop:** I follow the guide and correct steps that fail on my environment.

**Validation:** Verify setup steps from a fresh clone or clean environment where feasible.

### 42. Explain a design decision
**Prompt**
> Help me explain the actual architecture and two or three important design choices. For each choice, state the problem, the chosen approach, an alternative, and the trade-off. Base the explanation on the current code and do not claim a pattern is implemented unless it is visible in the repository.

**Human-in-the-loop:** I ensure I understand and can defend every decision in my own words.

**Validation:** Link each explanation to a relevant source file, test, or configuration.

### 43. Document limitations honestly
**Prompt**
> Help me classify features as implemented, partially implemented, not implemented, or not tested based on the source and evidence I provide. Identify operational limitations and edge cases. Do not describe planned work as completed work.

**Human-in-the-loop:** I correct statuses that overstate what the application can do.

**Validation:** Check every claim against the code and test results.

### 44. Create reviewer verification steps
**Prompt**
> Write a concise verification checklist using actual repository commands. Include prerequisites, setup, starting the application, running tests, and checking key behavior. Give an observable expected result for each step and mark any step that depends on external credentials or services.

**Human-in-the-loop:** I run each step and remove or correct any instruction that is not reproducible.

**Validation:** Keep the checklist aligned with actual behavior.

### 45. Inspect the final diff for risk
**Prompt**
> Review the current Git diff for secrets, generated files, unrelated edits, weakened tests, unsupported README claims, and accidental deployment changes. Group findings by severity and recommend the smallest safe corrections. Base the review on the actual diff, not assumptions about files you have not seen.

**Human-in-the-loop:** I inspect the findings and decide which changes to accept.

**Validation:** Re-run relevant tests after corrections and inspect the diff again.

---

## Phase 8 — Git history, AI transparency, and final review

### 46. Create truthful, meaningful commits
**Prompt**
> Review the actual changes and suggest logical commit groupings with accurate messages. Do not fabricate development history, backdate commits, or split changes merely to make the history look larger. Group related real changes such as documentation, tests, or fixes.

**Human-in-the-loop:** I decide when a change is ready and commit only work that actually happened.

**Validation:** Check `git status` and `git log --oneline` after committing.

### 47. Record AI's role accurately
**Prompt**
> Help me document each real AI interaction by separating my prompt, the response or code suggestion, what I personally accepted or changed, and how I checked it. Mark reconstructed wording clearly. Do not invent prompts, decisions, test results, or claims about independent implementation.

**Human-in-the-loop:** I compare the log with the conversations and my code changes and remove inaccurate entries.

**Validation:** Check that the document is honest and that evidence supports its claims.

### 48. Prepare to explain the work myself
**Prompt**
> Interview me one question at a time about the architecture, models, validation, scheduling, workflow, offers, persistence, tests, deployment, and limitations. Ask me to explain why I chose each approach and what alternatives I considered. Correct misunderstandings, but do not write fictional personal experience for me.

**Human-in-the-loop:** I answer in my own words and study any concept I cannot explain confidently.

**Validation:** Rehearse against the actual source code.

### 49. Rehearse a technical walkthrough
**Prompt**
> Build a short walkthrough of the actual repository: the problem, architecture, one representative business flow, validation and tests, deployment, AI assistance, and known limitations. For each claim, identify a file, test, command, or live behavior that demonstrates it. Flag any claim without evidence.

**Human-in-the-loop:** I rehearse the flow and remove claims I cannot demonstrate.

**Validation:** Run the walkthrough using the current code and deployment.

### 50. Perform a criteria-based submission audit
**Prompt**
> Audit the repository against the submission criteria: executable code, reproducible setup, meaningful genuine Git history, public repository, transparent AI prompt history, visible reasoning, test evidence, limitations, and readiness for a walkthrough. Mark each criterion verified, partially verified, or not verified, and cite the artifact or command that supports the status. Do not treat a README statement alone as proof that behavior works.

**Human-in-the-loop:** I decide what must be fixed before submission and avoid marking unsupported items complete.

**Validation:** Save the final audit with actual results and remaining gaps.

---

## Prompt-to-evidence traceability table

Use this table for the prompts that materially affected the delivered project. It is better to complete 8–15 well-evidenced entries than to invent evidence for all 50.

| Prompt # | Prompt status | Related file/commit | Human decision or change | Validation evidence |
|---|---|---|---|---|
| [#] | [Original / reconstructed / proposed] | [Path or commit] | [What I accepted, changed, or rejected] | [Actual test/command/output] |
| [#] | [Original / reconstructed / proposed] | [Path or commit] | [What I accepted, changed, or rejected] | [Actual test/command/output] |
| [#] | [Original / reconstructed / proposed] | [Path or commit] | [What I accepted, changed, or rejected] | [Actual test/command/output] |

## Human contribution summary — fill in with real details

- **Requirements I personally clarified:** [Describe actual decisions.]
- **Architecture decisions I made:** [Describe choices and trade-offs you can explain.]
- **Code I reviewed or changed after AI suggestions:** [Give real files or examples.]
- **AI suggestions I rejected or corrected:** [Give a real example, or state that none has been recorded.]
- **Tests I actually ran:** [Add exact command and actual summary.]
- **Deployment checks I actually performed:** [Add real status, route, and browser observations.]
- **Known limitations:** [List real gaps and unverified behavior.]

## Evidence log

| Date/time | Evidence | Actual result | Status |
|---|---|---|---|
| [Fill in] | [Test command/output] | [Actual observation] | [Pass/fail/not run] |
| [Fill in] | [Health/API request] | [Actual status/body] | [Observed result] |
| [Fill in] | [Frontend manual check] | [Actual behavior] | [Observed result] |
| [Fill in] | [Git commit/diff] | [Actual change] | [Committed/not committed] |

**Submission integrity:** This is a structured reconstruction to help organize the project's prompt-engineering process; it is not a historical transcript. Do not submit the 50 entries as proof that all 50 were used. For the strongest and most credible submission, label each entry as one of: **Original prompt** (verbatim from history), **Reconstructed from actual work** (wording recreated from a real interaction), or **Proposed workflow** (a useful prompt that was not necessarily used). Keep the third category out of claims about past AI usage. For every completed entry, add a real artifact, diff, command, test result, or decision where possible. Record failed attempts and corrections too; honest iteration is stronger evidence than a perfect-looking story.
=======
\# AI Prompt History and Development Disclosure



\## 1. Purpose



This document summarizes the AI-assisted development activities used during the Recruitment Management System challenge.



\*\*Important disclosure:\*\* This is a reconstructed summary of the development workflow, not a complete verbatim export of every prompt submitted to every AI tool. Individual prompts and responses may not all have been preserved.



\## 2. Areas Where AI Assistance Was Used



AI assistance was used to help with development and troubleshooting activities such as:



\- Reviewing application structure and separation of responsibilities.

\- Discussing recruitment workflow features and implementation options.

\- Troubleshooting frontend dependency installation and production-build issues.

\- Reviewing deployment configuration and API connectivity.

\- Improving setup instructions, testing documentation, and submission readiness.

\- Drafting documentation describing architecture, tests, limitations, and development decisions.



These are summaries of assistance areas, not guaranteed verbatim prompts.



\## 3. Representative Prompt Themes



The following are representative summaries of prompt themes, not exact historical quotations:



1\. Review a recruitment management system project structure and identify missing implementation or documentation work.

2\. Troubleshoot frontend dependency installation and make `npm ci` succeed.

3\. Diagnose and resolve frontend production-build errors.

4\. Check API deployment configuration and frontend-to-backend connectivity.

5\. Organize testing evidence and document which checks passed and which remain unverified.

6\. Review Git changes and prepare a safe submission without committing environment secrets.

7\. Prepare architecture and AI-usage disclosure documentation.



\## 4. Where AI Accelerated Development



AI assistance helped accelerate troubleshooting, organize technical checks, explain command-line output, and draft documentation.



\## 5. What the Developer Must Personally Verify



The developer remains responsible for understanding and validating the submitted work, including:



\- Reviewing the code and its behavior.

\- Running tests and checking the actual command output.

\- Confirming deployment behavior in the browser.

\- Reviewing configuration and ensuring no secrets are committed.

\- Understanding the architecture, design trade-offs, and limitations.

\- Being able to explain the implementation during a project review.



\## 6. Limitations of This Record



This document does not claim to preserve every original prompt, response, or timestamp. It should be supplemented with original prompt exports or notes if they are available.



No AI-generated statement should be treated as proof that a feature works unless supported by actual code inspection or test evidence.
>>>>>>> fd555ee (docs: prepare recruitment system submission)
