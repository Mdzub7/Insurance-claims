# Cloud-Native Insurance Claim Filing System

## Overview
Modern claims portal with patient and admin experiences. Frontend is static (HTML/CSS/JS) and themed to match Cigna styling; backend is FastAPI with AWS Services integrations DynamoDB, S3, Secrets manager, Lambda, SQS etc.

## Quick Start
- Frontend:
  - `cd frontend`
  - `python3 -m http.server 8080`
  - Open `http://localhost:8080/index.html`
- Backend:
  - `cd backend`
  - `python -m venv .venv && source .venv/bin/activate`
  - `pip install -r requirements.txt`
  - Configure AWS credentials and set Secrets Manager JWT secret per `backend/app/core/config.py`.
  - Run: `uvicorn app.main:app --reload --port 8001`

## Documentation
- Frontend: [README.frontend.md](./README.frontend.md) — layouts, pages, auth guards, charts.
- Backend: [README.backend.md](./README.backend.md) — endpoints, data model, AWS setup.

## Pages and Flows
- Home + Member Guide (demo access).
- Patient portal: Profile, Dashboard (KPIs/charts), Claims History (filters + timeline), Submit Claim (INR, dropzone), Claim Lifecycle.
- Admin portal: Profile, Dashboard (pending KPIs/charts with polling), Claims (pending table + approve/reject + patient search), Analytics (year/user filters, monthly amounts, status donut, top users).

## Endpoints Used
- Auth: `/api/v1/auth/login`, `/api/v1/auth/register`, `/api/v1/users/me`
- Claims: `/api/v1/claims/` (POST), `/api/v1/claims/my` (GET)
- Admin: `/api/v1/admin/users`, `/api/v1/admin/claims/pending`, approve/reject under `/api/v1/admin/claims/{id}/...`

## Testing
- Backend tests in `backend/tests/` — run `pytest` or `python run_tests.py`.
- Optional UI checks with Playwright from `frontend`: `npx playwright test`.

## Deployment Checklist
- Terraform: SQS, DynamoDB, Lambda, IAM; enable S3 bucket and notifications if uploads are needed.
- Secrets Manager configured and IAM access granted.
- CORS configured for frontend origin.

## Notes
- Lambda, Bedrock.
- For full admin analytics across all statuses, add an endpoint to list claims or query by status; current UI uses available endpoints (pending + users) and polls for real-time updates.
