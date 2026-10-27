# Testing and Verification

## Recruitment Management System

This document records the automated tests and manual checks performed for the Recruitment Management System. It distinguishes verified results from checks that still require evidence.

## 1. Environment and Deployment

| Item | Details |
|---|---|
| Local project directory | `D:\yottaflex.ai` |
| Git branch | `main` |
| Frontend | React + Vite |
| Backend | FastAPI |
| Frontend hosting | Vercel |
| Backend hosting | Render |
| Frontend URL | https://recruitment-management-system-three.vercel.app/ |
| Backend URL | https://recruitment-management-system-api.onrender.com |
| API documentation | https://recruitment-management-system-api.onrender.com/docs |
| Backend health endpoint | https://recruitment-management-system-api.onrender.com/health |

Never commit `.env` contents, passwords, API keys, tokens, or private connection strings.

## 2. Repository Test Files

The following test files were present in the repository:

- `tests/conftest.py`
- `tests/test_generation.py`
- `tests/test_models.py`
- `tests/test_offers.py`
- `tests/test_reproducibility.py`
- `tests/test_scheduling.py`
- `tests/test_screening.py`
- `tests/test_validation.py`
- `tests/test_workflow.py`

These files cover areas including data generation, database models, offers, reproducibility, scheduling, screening, validation, and recruitment workflow transitions. Their presence does not guarantee that every business requirement or possible failure scenario is covered.

## 3. Python Automated Tests

**Command executed from the project root:**

```bash
python -m pytest -v
```

**Recorded results:**

| Metric | Result |
|---|---:|
| Tests collected | 19 |
| Tests passed | 19 |
| Tests failed | 0 |
| Runtime | 11.38 seconds |
| Python version | 3.11.0 |
| pytest version | 9.1.1 |

**Status: Passed.** All 19 tests completed successfully in the recorded run.

To repeat the test:

```bash
python -m pytest -v
```

This result applies to the environment and code tested at that time. It does not independently verify every deployed API route or frontend workflow.

## 4. Frontend Dependency Installation

**Command executed from the `frontend` directory:**

```bash
npm ci
```

**Recorded results:**

- Dependency installation completed successfully.
- npm reported 0 vulnerabilities.

**Status: Passed**, based on the recorded command output.

To repeat this check from the repository root:

```bash
cd frontend
npm ci
```

## 5. Frontend Production Build

**Command executed from the `frontend` directory:**

```bash
npm run build
```

**Recorded results:**

- Vite production build completed successfully.
- 17 modules were transformed.
- Build duration was approximately 140 ms.

**Status: Passed**, based on the recorded command output.

To repeat this check:

```bash
cd frontend
npm run build
```

A successful local build does not by itself confirm that the latest version has been deployed successfully to Vercel. The deployed frontend should be checked after the latest repository changes.

## 6. Backend Health Check

**Endpoint:**

https://recruitment-management-system-api.onrender.com/health

**Command used:**

```bash
curl.exe -i https://recruitment-management-system-api.onrender.com/health
```

**Previously observed response:**

```http
HTTP/1.1 200 OK
```

The response body reported:

```json
{
  "status": "UP",
  "service": "recruitment-management-system",
  "database": "HEALTHY",
  "version": "1.0.0"
}
```

**Status: Verified at the recorded time.** The endpoint returned HTTP 200 and reported that the application was up and the database was healthy.

This result does not guarantee that all API routes or application features are working correctly now.

**Before submission:** Run the health check again and record the current result.

## 7. CORS Verification

The following request was previously tested:

```bash
curl.exe -i -H "Origin: https://recruitment-management-system-three.vercel.app" https://recruitment-management-system-api.onrender.com/health
```

The observed response included:

```http
HTTP/1.1 200 OK
access-control-allow-origin: https://recruitment-management-system-three.vercel.app
vary: Origin
```

The response also reported the application status as `UP` and the database status as `HEALTHY`.

**Status: Verified for the tested origin and `/health` request at the time checked.**

This check does not prove that all API endpoints, browser preflight requests, or application workflows are configured correctly.

## 8. Frontend and Backend Manual Verification

The browser Console previously showed a failed request to the backend health endpoint with the error:

```text
net::ERR_BLOCKED_BY_CLIENT
```

The user subsequently reported that the site connected in Incognito mode. Browser-side blocking, such as an extension or privacy filter, is a possible explanation, but the exact cause was not conclusively established.

Before submission, perform the following checks:

- [ ] Open the deployed frontend.
- [ ] Confirm that the page renders without a blank screen.
- [ ] Confirm that API requests use the deployed Render URL rather than `localhost`.
- [ ] Check the health endpoint response.
- [ ] Check application-data API requests.
- [ ] Review the browser Console for unexplained errors.
- [ ] Confirm that the dashboard displays the expected data when the API is available.
- [ ] Complete at least one supported recruitment workflow from start to finish.
- [ ] Compare normal browsing and Incognito mode if `ERR_BLOCKED_BY_CLIENT` recurs.

**Status:** A complete end-to-end frontend workflow result has not been recorded. Do not mark the entire frontend as fully tested until this verification is completed.

## 9. Troubleshooting Notes

### CORS errors

1. Check the exact frontend origin in the browser address bar.
2. Inspect the failing request in DevTools → Network.
3. Check whether an `OPTIONS` preflight request is failing.
4. Inspect the `access-control-allow-origin` response header.
5. Review the backend CORS configuration if the observed request indicates a configuration issue.

A successful CORS check on `/health` does not prove that every endpoint and preflight request works.

### `net::ERR_BLOCKED_BY_CLIENT`

This error can indicate client-side blocking, such as an extension or privacy filter. It does not identify a particular extension by itself.

1. Compare normal browsing with Incognito mode.
2. Check whether extensions are enabled in Incognito.
3. If necessary, test extensions one at a time.
4. Recheck the failing request in DevTools → Network.

Do not repeatedly redeploy the backend without evidence that the problem originates from the backend.

### Health check succeeds but the UI shows “disconnected”

Inspect the exact failing request. The health endpoint can work while another API endpoint fails because of a route error, unexpected response format, server error, or browser restriction.

## 10. Known Verification Gaps

| Check | Available evidence | Status |
|---|---|---|
| Python automated tests | 19 passed, 0 failed | Passed |
| Frontend dependency installation | `npm ci` succeeded; 0 vulnerabilities reported | Passed |
| Frontend production build | Vite build succeeded; 17 modules transformed | Passed |
| Backend health endpoint | HTTP 200; application `UP`; database `HEALTHY` | Verified at the recorded time |
| CORS for Vercel origin | Matching origin header on `/health` | Verified for the tested request |
| All API routes | Complete route-by-route results not recorded | Not fully verified |
| Frontend end-to-end workflow | Complete workflow result not recorded | Not verified |
| Fresh-clone installation | Clean-environment test not recorded | Not verified |
| Latest Vercel deployment | Final verification after the latest repository changes not recorded | Recheck required |
| Browser-side request blocking | `ERR_BLOCKED_BY_CLIENT` observed; Incognito reportedly worked | Exact cause unconfirmed |

These gaps do not necessarily indicate defects. They identify checks for which complete evidence has not been recorded.

## 11. Final Evidence Summary

The Python automated test suite and frontend production build passed in the recorded runs. Frontend dependencies were installed successfully, and npm reported no vulnerabilities. The backend health endpoint and CORS response were also verified for the specific requests described above.

A complete end-to-end frontend workflow, every API route, a fresh-clone setup, and the latest deployed frontend still require verification.

## 12. Submission Standard

A check should be marked **verified** only for the specific command, route, environment, and time actually tested.

A successful test suite provides evidence for the scenarios it covers. A successful health check verifies the health endpoint at the time tested. Neither result guarantees that every deployed feature works correctly.

If a check has not been performed, mark it **Not verified**. If a check fails, preserve the result and document the next step. This evidence-based approach makes the submission more transparent and credible.
