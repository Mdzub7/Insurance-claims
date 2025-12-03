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
- GitHub Actions CI/CD: automated tests, Terraform deploy, and Docker build/push to ECR.

## CI/CD
- GitHub Actions Workflows:
  - `.github/workflows/ci.yml`: Backend tests on push/PR.
  - `.github/workflows/terraform.yml`: Terraform init/validate/plan/apply for `terraform/` on main.
  - `.github/workflows/docker-ecr.yml`: Build and push `backend` and `frontend` images to ECR on main.
- Required repository secrets:
  - `AWS_REGION`: AWS region
  - `AWS_OIDC_ROLE`: IAM Role ARN for GitHub OIDC (recommended) or configure access keys
  - `ECR_BACKEND`: ECR repo URI for backend, e.g. `<account>.dkr.ecr.<region>.amazonaws.com/claims-backend`
  - `ECR_FRONTEND`: ECR repo URI for frontend, e.g. `<account>.dkr.ecr.<region>.amazonaws.com/claims-frontend`

## Containerization and Kubernetes
- Build locally:
  - Backend: `cd backend && docker build -t claims-backend:latest .`
  - Frontend: `cd frontend && docker build -t claims-frontend:latest .`
- Push to ECR:
  - Login: `aws ecr get-login-password --region <REGION> | docker login --username AWS --password-stdin <ACCOUNT>.dkr.ecr.<REGION>.amazonaws.com`
  - Tag + push backend: `docker tag claims-backend:latest <ACCOUNT>.dkr.ecr.<REGION>.amazonaws.com/claims-backend:latest && docker push <ACCOUNT>.dkr.ecr.<REGION>.amazonaws.com/claims-backend:latest`
  - Tag + push frontend: `docker tag claims-frontend:latest <ACCOUNT>.dkr.ecr.<REGION>.amazonaws.com/claims-frontend:latest && docker push <ACCOUNT>.dkr.ecr.<REGION>.amazonaws.com/claims-frontend:latest`
- EKS deploy:
  - `aws eks --region <REGION> update-kubeconfig --name <CLUSTER>`
  - Apply deployments/services for two replicas each and connect via ClusterIP/LoadBalancer.

## Architecture & Demo Script
- Clean Architecture: Routers call Services; Services use Repositories (boto3) to AWS.
- Auth: FastAPI dependency with JWT signed via Secrets Manager; role-based routing.
- Claims: Submit → S3 document upload → Lambda → SQS; Admin review approve/reject.
- Demo flow:
  - Start backend (`uvicorn`) and frontend (`http.server`).
  - Register/login; see role-based portal.
  - Patient submits a claim with PDF; document view link appears.
  - Admin dashboard shows pending; approve/reject; analytics update.

## Viva Prep
- GitHub Actions: purpose, triggers, OIDC to AWS, artifacts vs deploy.
- Terraform: state, plan/apply, single table DynamoDB design.
- FastAPI: dependency injection, pydantic schemas, async endpoints.
- AWS: Secrets Manager (JWT), DynamoDB (GSI), S3 presigned URLs, Lambda→SQS.
- Containers: image layering, ECR registry, EKS services.

## Notes
- Lambda, Bedrock.
- For full admin analytics across all statuses, add an endpoint to list claims or query by status; current UI uses available endpoints (pending + users) and polls for real-time updates.
