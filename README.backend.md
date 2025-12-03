# Backend

## Overview
FastAPI service with AWS integrations (DynamoDB, Secrets Manager). Provides auth, user, claim submission, and admin endpoints.

## Key Endpoints
- `POST /api/v1/auth/login` — Login with email or patient_id + password.
- `POST /api/v1/auth/register` — Register user; returns patient_id for patients.
- `GET /api/v1/users/me` — Current user profile.
- `POST /api/v1/claims/` — Submit claim; returns presigned S3 URL (temporarily disabled in UI).
- `GET /api/v1/claims/my` — Claims of the current user.
- Admin:
  - `GET /api/v1/admin/users` — List users.
  - `GET /api/v1/admin/claims` — List all claims; optional `status` query.
  - `GET /api/v1/admin/claims/pending` — Pending claims.
  - `GET /api/v1/admin/claims/by-patient/{patient_id}` — Claims for a patient.
  - `POST /api/v1/admin/claims/{id}/approve` — Approve claim.
  - `POST /api/v1/admin/claims/{id}/reject` — Reject claim.

## Data Model (DynamoDB)
- Users stored as items with `claim_id` key prefixed `USER#{user_id}` and fields like `email`, `role`, `patient_id`.
- Claims stored with `claim_id` key (e.g., `CLAIM#...`), `user_id`, `amount`, `description`, `claim_status`, `created_at`, `s3_upload_url`.

## AWS
- Region: configured in `backend/app/core/config.py`.
- Secrets Manager: JWT signing secret.
- DynamoDB: single table pattern.
- S3: presigned URLs generated on claim creation; UI currently hides upload control.

## Running Locally
- `cd backend && pip install -r requirements.txt`
- Run FastAPI (example): `uvicorn app.main:app --reload --port 8001`
- Ensure AWS credentials are configured (`aws configure`).

## CI
- GitHub Actions runs backend tests on push/PR via `.github/workflows/ci.yml`.
- Configure `AWS_REGION`, `AWS_OIDC_ROLE` for Terraform and ECR workflows.

## Tests
- `backend/tests` — basic tests for auth/claims.
- Run: `python -m pytest` or `python run_tests.py`.

## Notes
- Admin analytics and dashboard use the all-claims endpoint for accurate totals, monthly aggregates, and status distribution. Patient search in Admin → Claims uses the by-patient endpoint.
