# Testing and Verification

## Recruitment Management System

This document records the verification evidence currently available for the project and gives reproducible commands for checks that still need to be run.

**Evidence rule:** Only observed results are marked as verified. The Python test suite and frontend production build have not been run in the evidence available for this document, so their results are explicitly marked **Not run / result not provided** rather than guessed.

## 1. Environment and deployment

| Item | Current information | Evidence/status |
|---|---|---|
| Local project directory | `D:\yottaflex.ai` | Confirmed in terminal output |
| Git branch | `main` | Confirmed by `git status` |
| Git synchronization | Local `main` was up to date with `origin/main` at the last status check | Confirmed by `git status` |
| Latest commit seen | `43c73bd` — `Fix deployed backend URL fallback` | Confirmed by `git log -5 --oneline` |
| Python virtual environment | `.venv` | Confirmed by the terminal prompt and activation command |
| Frontend | React + Vite, under `frontend/` | Known project configuration |
| Backend | FastAPI, deployed on Render | Confirmed by the deployed health response and project context |
| Frontend hosting | Vercel | Confirmed by the deployed frontend URL and project context |
| Backend health URL | `https://recruitment-management-system-api.onrender.com/health` | Confirmed endpoint |
| Frontend origin checked for CORS | `https://recruitment-management-system-three.vercel.app` | Confirmed by the user's `curl.exe` command |
| Python version | Not recorded in the evidence available here | Run `python --version` |
| Node.js/npm versions | Not recorded in the evidence available here | Run `node --version` and `npm --version` |

Never include `.env` contents, database passwords, API keys, tokens, or private connection strings in this file or in public GitHub issues.

## 2. Repository test files

The local repository listing showed these test files:

- `tests/conftest.py`
- `tests/test_generation.py`
- `tests/test_models.py`
- `tests/test_offers.py`
- `tests/test_reproducibility.py`
- `tests/test_scheduling.py`
- `tests/test_screening.py`
- `tests/test_validation.py`
- `tests/test_workflow.py`

This confirms that test files exist for these areas; it does **not** establish that every test passes or that every business requirement is covered.

## 3. Install dependencies

From Windows Command Prompt, open the repository root:

```bat
cd /d D:\yottaflex.ai
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
```

Install frontend dependencies:

```bat
cd frontend
npm ci
cd ..
```

**Result:** Dependency-installation output has not been provided in the evidence available for this document. Run these commands if setup needs to be revalidated, and record any errors accurately.

## 4. Automated Python tests

Run from the repository root with `.venv` activated:

```bat
python -m pytest -v
```

Optional coverage command, if `pytest-cov` is installed:

```bat
python -m pytest --cov=src --cov-report=term-missing
```

| Check | Result | Status |
|---|---|---|
| Python test suite (`python -m pytest -v`) | Test output was not provided; no pass/fail count can be claimed | **Not verified** |
| Coverage report | No coverage output was provided | **Not run / not verified** |

After running pytest, replace this row with the exact summary printed by pytest, including passed, failed, skipped, and error counts. If any tests fail, retain that information and document the next step rather than hiding the failure.

## 5. Frontend production build

Run:

```bat
cd /d D:\yottaflex.ai\frontend
npm ci
npm run build
```

**Result:** A production-build output was not provided in the evidence available for this document.

| Check | Result | Status |
|---|---|---|
| Vite production build (`npm run build`) | Build output not provided | **Not verified** |

A successful build should complete without a build error and produce the configured output directory, typically `dist/`. Confirm the actual output rather than assuming success.

## 6. Deployed backend health check

### Observed result

The user ran the following command in Windows Command Prompt:

```bat
curl.exe -i https://recruitment-management-system-api.onrender.com/health
```

Observed output included:

```text
HTTP/1.1 200 OK
access-control-allow-credentials: true
x-render-origin-server: uvicorn
```

The response body was:

```json
{
  "status": "UP",
  "service": "recruitment-management-system",
  "database": "HEALTHY",
  "version": "1.0.0"
}
```

**Status: Verified for that check.** The response timestamp shown by the command was `Tue, 27 Oct 2026 15:36:37 GMT` (21:06:37 India Standard Time). This verifies the health endpoint's reported state at that time; it does not guarantee that every API route or frontend operation succeeds now.

### Re-run before submission

```bat
curl.exe -i https://recruitment-management-system-api.onrender.com/health
```

Record the current status and body after running the command again.

## 7. CORS response check

### Observed result

The user ran:

```bat
curl.exe -i -H "Origin: https://recruitment-management-system-three.vercel.app" https://recruitment-management-system-api.onrender.com/health
```

The observed response included:

```text
HTTP/1.1 200 OK
access-control-allow-credentials: true
access-control-allow-origin: https://recruitment-management-system-three.vercel.app
vary: Origin
```

The JSON response reported `status: UP` and `database: HEALTHY`.

**Status: Verified for this origin and the `/health` response at the time of the check.** This does not prove that all endpoints, browser preflight requests, or application workflows are configured correctly.

## 8. Frontend/API browser checks

### Evidence observed

The browser Console screenshot showed a failed request to:

```text
GET https://recruitment-management-system-api.onrender.com/health
net::ERR_BLOCKED_BY_CLIENT
```

The user later reported that the site connected in Incognito. This makes browser-side blocking, such as an extension or privacy filter, a plausible explanation for the normal-window issue, but the exact cause was not established by the available evidence.

### Manual verification checklist

Complete these checks in the deployed frontend:

- [ ] Open `https://recruitment-management-system-three.vercel.app/`.
- [ ] Confirm the page renders without a blank screen.
- [ ] Open DevTools → Network and confirm requests use the Render API URL rather than `localhost`.
- [ ] Check the status and response of `/health`.
- [ ] Check the status and response of application-data requests, not just `/health`.
- [ ] Check DevTools → Console for unexplained application errors.
- [ ] Confirm the dashboard displays the expected data when the API is available.
- [ ] Exercise at least one supported recruitment workflow end-to-end.
- [ ] Compare normal browsing and Incognito if `ERR_BLOCKED_BY_CLIENT` recurs.

**Status:** The browser error and the successful Incognito behavior were reported/observed in the conversation, but a complete end-to-end frontend workflow result has not been supplied. Do not mark the entire frontend as fully tested yet.

## 9. Troubleshooting guidance

### CORS error

1. Check the exact origin in the browser address bar.
2. Inspect the failing request and any `OPTIONS` preflight request in DevTools → Network.
3. Check the response's `access-control-allow-origin` header.
4. Check the backend CORS configuration only if the observed request supports that diagnosis.

A successful CORS header on `/health` does not prove that every endpoint and preflight request works.

### `net::ERR_BLOCKED_BY_CLIENT`

This error can indicate client-side blocking, such as an extension or privacy filter. It does not identify a particular extension by itself.

1. Compare normal browsing and Incognito.
2. Check whether extensions are enabled in Incognito.
3. If needed, test one extension at a time.
4. Recheck the same request in DevTools.

Do not repeatedly redeploy the backend if the evidence points to a browser-side block.

### Health succeeds but the UI says “disconnected”

Inspect the exact failing request. The health endpoint can work while another endpoint fails because of a different route, response format, authorization requirement, server error, or browser restriction.

## 10. Known verification gaps

Based on the evidence currently available:

- **Python tests:** Test files exist, but the latest full-suite result has not been provided.
- **Frontend build:** A current `npm run build` result has not been provided.
- **Health endpoint:** A successful `HTTP 200 OK` result was observed on 27 October 2026.
- **CORS:** The tested Vercel origin was returned in the CORS header for `/health`.
- **Full API coverage:** Not established by the health check alone.
- **Full frontend workflow:** No complete end-to-end test result has been provided.
- **Clean-install reproduction:** Not established from a fresh clone or clean environment.
- **Browser-side block:** `ERR_BLOCKED_BY_CLIENT` was observed and Incognito reportedly worked; the exact extension/cause was not conclusively identified.

These are evidence gaps, not necessarily application defects. Update them after running the corresponding checks.

## 11. Final evidence summary

| Check | Current evidence | Status |
|---|---|---|
| Git working tree and branch | `git status` showed `main`, up to date with `origin/main`, and a clean working tree at the time of the check | Verified at that time |
| Test files present | Multiple test modules were listed under `tests/` | Verified; passing status unknown |
| Python test suite | No latest test output supplied | Not verified |
| Frontend build | No latest build output supplied | Not verified |
| Backend `/health` | `HTTP 200 OK`; `status: UP`; `database: HEALTHY` | Verified at recorded time |
| CORS for tested Vercel origin on `/health` | Matching `access-control-allow-origin` header | Verified for that request |
| Full API routes | No complete route-by-route results supplied | Not verified |
| Full frontend workflow | No end-to-end result supplied | Not verified |
| Fresh-clone setup | No clean-environment result supplied | Not verified |

## 12. Submission standard

A check is marked **verified** only for the specific command, route, environment, and time actually tested. A successful health endpoint is not proof that the whole system works. If a command has not been run, mark it **Not verified**. If it fails, preserve the result and explain the next step. This evidence-based approach is more credible than claiming that every check passed without output.
